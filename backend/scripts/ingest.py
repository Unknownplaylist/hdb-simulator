"""Seed the DB from the bundled GeoJSON. Idempotent."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app import models  # noqa: E402


def polygon_centroid(coords):
    ring = coords[0]
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def polygon_area_m2(coords):
    ring = coords[0]
    s = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0 * (111_000 ** 2)


def main(buildings_path: str, units_path: str | None):
    Base.metadata.create_all(bind=engine)

    with open(buildings_path) as f:
        fc = json.load(f)

    unit_lookup: dict[tuple[str, str], dict] = {}
    if units_path and Path(units_path).exists():
        with open(units_path) as f:
            units_data = json.load(f)
        for row in units_data:
            key = (str(row.get("blk_no", "")).upper(), str(row.get("street", "")).upper())
            unit_lookup[key] = row

    db = SessionLocal()
    inserted = 0
    try:
        db.query(models.Building).delete()
        for feat in fc["features"]:
            props = feat["properties"]
            geom = feat["geometry"]
            gtype = geom["type"]

            if gtype == "Polygon":
                lon, lat = polygon_centroid(geom["coordinates"])
                area = polygon_area_m2(geom["coordinates"])
            elif gtype == "Point":
                lon, lat = geom["coordinates"][0], geom["coordinates"][1]
                area = float(props.get("footprint_area") or 400.0)
            else:
                continue

            blk = str(props.get("blk_no", "")).strip()
            street = str(props.get("street", "")).strip()
            postal = str(props.get("postal_code", "")).strip()
            height = float(props.get("height_m") or props.get("AGL") or 30.0)

            ul = unit_lookup.get((blk.upper(), street.upper()), {})
            db.add(models.Building(
                block_no=blk,
                street=street,
                postal_code=postal,
                lon=lon, lat=lat, height_m=height, footprint_area=area,
                units_1r=int(ul.get("units_1r", props.get("units_1r", 0)) or 0),
                units_2r=int(ul.get("units_2r", props.get("units_2r", 0)) or 0),
                units_3r=int(ul.get("units_3r", props.get("units_3r", 0)) or 0),
                units_4r=int(ul.get("units_4r", props.get("units_4r", 0)) or 0),
                units_5r=int(ul.get("units_5r", props.get("units_5r", 0)) or 0),
            ))
            inserted += 1
            if inserted % 2000 == 0:
                db.commit()
        db.commit()
    finally:
        db.close()

    print(f"Ingested {inserted} buildings.")


if __name__ == "__main__":
    buildings = sys.argv[1] if len(sys.argv) > 1 else "data/buildings_sample.geojson"
    units = sys.argv[2] if len(sys.argv) > 2 else None
    main(buildings, units)
