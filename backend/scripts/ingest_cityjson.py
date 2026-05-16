"""Ingest the ualsg/hdb3d-data CityJSON dataset (SVY21 -> WGS84)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from pyproj import Transformer
except ImportError:  # pragma: no cover
    print("Missing dep. Install with:  pip install pyproj")
    sys.exit(1)

from app.database import Base, SessionLocal, engine  # noqa: E402
from app import models  # noqa: E402

SVY21_TO_WGS84 = Transformer.from_crs("EPSG:3414", "EPSG:4326", always_xy=True)


def real_vertices(cityjson) -> list[tuple[float, float, float]]:
    t = cityjson.get("transform", {"scale": [1, 1, 1], "translate": [0, 0, 0]})
    sx, sy, sz = t["scale"]
    tx, ty, tz = t["translate"]
    return [(v[0] * sx + tx, v[1] * sy + ty, v[2] * sz + tz) for v in cityjson["vertices"]]


def ground_footprint(geometry: list, verts: list) -> list[tuple[float, float]]:
    # LoD 1.2 is an extruded prism; the bottom face has the lowest mean z.
    for g in geometry:
        boundaries = g.get("boundaries", [])
        gtype = g.get("type", "")
        if gtype == "Solid":
            surfaces = boundaries[0] if boundaries else []
        elif gtype in ("MultiSurface", "CompositeSurface"):
            surfaces = boundaries
        else:
            continue

        best_ring, best_z = None, float("inf")
        for surface in surfaces:
            outer_ring = surface[0] if surface else []
            if not outer_ring:
                continue
            mean_z = sum(verts[vi][2] for vi in outer_ring) / len(outer_ring)
            if mean_z < best_z:
                best_z = mean_z
                best_ring = [(verts[vi][0], verts[vi][1]) for vi in outer_ring]
        if best_ring:
            return best_ring
    return []


def shoelace_area(ring: list[tuple[float, float]]) -> float:
    if len(ring) < 3:
        return 0.0
    s = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def centroid(ring: list[tuple[float, float]]) -> tuple[float, float]:
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def units_from_attrs(a: dict, room: int) -> int:
    # Rental variants only exist for 1- and 2-room in the source dataset.
    sold = int(a.get(f"hdb_{room}room_sold") or 0)
    rental = int(a.get(f"hdb_{room}room_rental") or 0)
    return sold + rental


def main(cityjson_path: str):
    Base.metadata.create_all(bind=engine)

    print(f"Loading CityJSON from {cityjson_path} ...")
    with open(cityjson_path) as f:
        cj = json.load(f)
    print(f"  CityJSON version: {cj.get('version')}")
    print(f"  Total CityObjects: {len(cj.get('CityObjects', {}))}")

    verts = real_vertices(cj)
    print(f"  Vertices: {len(verts)}")

    db = SessionLocal()
    db.query(models.Building).delete()

    inserted = 0
    skipped_no_geom = 0
    non_residential = 0

    for obj_id, obj in cj["CityObjects"].items():
        if obj.get("type") != "Building":
            continue

        attrs = obj.get("attributes", {})
        ring = ground_footprint(obj.get("geometry", []), verts)
        if not ring:
            skipped_no_geom += 1
            continue

        is_residential = str(attrs.get("hdb_residential", "")).upper() == "Y"
        if not is_residential:
            non_residential += 1

        cx_svy, cy_svy = centroid(ring)
        area_m2 = shoelace_area(ring)
        lon, lat = SVY21_TO_WGS84.transform(cx_svy, cy_svy)

        b = models.Building(
            block_no=str(attrs.get("hdb_blk_no") or "").strip(),
            street=str(attrs.get("hdb_street") or "").strip(),
            postal_code=str(attrs.get("osm_addr_postcode") or attrs.get("hdb_postal") or "").strip(),
            lon=lon, lat=lat,
            height_m=float(attrs.get("height") or 30.0),
            footprint_area=area_m2,
            units_1r=units_from_attrs(attrs, 1) if is_residential else 0,
            units_2r=units_from_attrs(attrs, 2) if is_residential else 0,
            units_3r=units_from_attrs(attrs, 3) if is_residential else 0,
            units_4r=units_from_attrs(attrs, 4) if is_residential else 0,
            units_5r=units_from_attrs(attrs, 5) if is_residential else 0,
        )
        db.add(b)
        inserted += 1
        if inserted % 1000 == 0:
            db.commit()

    db.commit()
    db.close()

    print(f"\nIngested {inserted} buildings.")
    print(f"  Non-residential (units set to 0): {non_residential}")
    print(f"  Skipped (no usable geometry):     {skipped_no_geom}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.ingest_cityjson path/to/hdb.json")
        sys.exit(2)
    main(sys.argv[1])
