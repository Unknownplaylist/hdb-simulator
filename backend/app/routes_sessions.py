from datetime import datetime

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.orm import Session as DBSession

from . import models, schemas, simulation
from .database import get_db

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[schemas.SessionOut])
def list_sessions(db: DBSession = Depends(get_db)):
    return db.scalars(select(models.Session).order_by(desc(models.Session.created_at))).all()


@router.post("", response_model=schemas.SessionOut)
def create_session(body: schemas.SessionCreate, db: DBSession = Depends(get_db)):
    s = models.Session(name=body.name, current_year=2025, status="created")
    db.add(s)
    db.commit()
    db.refresh(s)
    _persist_snapshot(db, s.id, 2025, _empty_state(db))
    return s


@router.get("/{session_id}", response_model=schemas.SessionOut)
def get_session(session_id: int, db: DBSession = Depends(get_db)):
    s = db.get(models.Session, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    return s


@router.delete("/{session_id}")
def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    s = db.get(models.Session, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    db.delete(s)
    db.commit()
    return {"ok": True}


@router.post("/{session_id}/randomize", response_model=schemas.SnapshotOut)
def randomize(session_id: int, db: DBSession = Depends(get_db)):
    s = db.get(models.Session, session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    buildings, units = _load_units(db)
    rng = np.random.default_rng()
    occupancy = simulation.random_assign(units, rng)
    residents = simulation.residents_from_occupancy(occupancy)

    state = _state_from_arrays(buildings, occupancy, residents,
                               births=0, deaths=0, moves=0, deaths_total=0)
    s.current_year = 2025
    s.status = "created"
    _persist_snapshot(db, session_id, s.current_year, state, replace=True)
    db.commit()
    return schemas.SnapshotOut(year=s.current_year, state=state)


@router.post("/{session_id}/tick", response_model=schemas.SnapshotOut)
def tick(session_id: int, db: DBSession = Depends(get_db)):
    s = db.get(models.Session, session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    buildings, units = _load_units(db)
    latest = db.scalar(
        select(models.Snapshot)
        .where(models.Snapshot.session_id == session_id)
        .order_by(desc(models.Snapshot.year))
    )
    if not latest:
        raise HTTPException(400, "Run /randomize first")

    occupancy = _occupancy_from_state(latest.state, buildings)
    rng = np.random.default_rng()
    result = simulation.tick(units, occupancy, rng)

    s.current_year += 1
    s.status = "running"
    prev_total_deaths = int(latest.state.get("totals", {}).get("deaths_total", 0))
    state = _state_from_arrays(buildings, result.new_occupancy, result.new_residents,
                               births=result.births, deaths=result.deaths,
                               moves=result.moves,
                               deaths_total=prev_total_deaths + result.deaths)
    _persist_snapshot(db, session_id, s.current_year, state)

    for src_idx, dst_idx, n in result.movement_records[:500]:
        m = models.Movement(
            session_id=session_id, year=s.current_year,
            from_building_id=int(buildings[src_idx].id),
            to_building_id=int(buildings[dst_idx].id),
            residents=int(n),
        )
        db.add(m)
    db.commit()
    return schemas.SnapshotOut(year=s.current_year, state=state)


@router.post("/{session_id}/pause", response_model=schemas.SessionOut)
def pause(session_id: int, db: DBSession = Depends(get_db)):
    s = db.get(models.Session, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    s.status = "paused"
    db.commit()
    return s


@router.get("/{session_id}/snapshots/{year}", response_model=schemas.SnapshotOut)
def get_snapshot(session_id: int, year: int, db: DBSession = Depends(get_db)):
    snap = db.scalar(
        select(models.Snapshot)
        .where(models.Snapshot.session_id == session_id, models.Snapshot.year == year)
    )
    if not snap:
        raise HTTPException(404, "Snapshot not found")
    return schemas.SnapshotOut(year=snap.year, state=snap.state)


@router.get("/{session_id}/snapshots", response_model=list[int])
def list_years(session_id: int, db: DBSession = Depends(get_db)):
    rows = db.scalars(
        select(models.Snapshot.year)
        .where(models.Snapshot.session_id == session_id)
        .order_by(models.Snapshot.year)
    ).all()
    return list(rows)


@router.get("/{session_id}/movements", response_model=list[schemas.MovementOut])
def get_movements(session_id: int, year: int, limit: int = 50, db: DBSession = Depends(get_db)):
    rows = db.scalars(
        select(models.Movement)
        .where(models.Movement.session_id == session_id, models.Movement.year == year)
        .limit(limit)
    ).all()
    return rows


def _load_units(db: DBSession):
    buildings = db.scalars(select(models.Building).order_by(models.Building.id)).all()
    if not buildings:
        raise HTTPException(503, "No buildings loaded. Run scripts/ingest.py first.")
    units = np.array(
        [[b.units_1r, b.units_2r, b.units_3r, b.units_4r, b.units_5r] for b in buildings],
        dtype=np.int32,
    )
    return buildings, units


def _empty_state(db: DBSession) -> dict:
    buildings, units = _load_units(db)
    occupancy = np.zeros_like(units)
    residents = np.zeros(units.shape[0], dtype=np.int32)
    return _state_from_arrays(buildings, occupancy, residents, 0, 0, 0, deaths_total=0)


def _state_from_arrays(buildings, occupancy, residents, births, deaths, moves,
                       deaths_total) -> dict:
    occ_map = {}
    for i, b in enumerate(buildings):
        o = occupancy[i]
        occ_map[str(b.id)] = {
            "u1": int(o[0]), "u2": int(o[1]), "u3": int(o[2]),
            "u4": int(o[3]), "u5": int(o[4]),
            "residents": int(residents[i]),
        }
    return {
        "occupancy": occ_map,
        "totals": {
            "residents": int(residents.sum()),
            "births_this_year": int(births),
            "deaths_this_year": int(deaths),
            "moves_this_year": int(moves),
            "deaths_total": int(deaths_total),
        },
    }


def _occupancy_from_state(state: dict, buildings) -> np.ndarray:
    occ_map = state.get("occupancy", {})
    arr = np.zeros((len(buildings), 5), dtype=np.int32)
    for i, b in enumerate(buildings):
        o = occ_map.get(str(b.id), {})
        arr[i] = [o.get("u1", 0), o.get("u2", 0), o.get("u3", 0), o.get("u4", 0), o.get("u5", 0)]
    return arr


def _persist_snapshot(db, session_id: int, year: int, state: dict, replace: bool = False):
    existing = db.scalar(
        select(models.Snapshot)
        .where(models.Snapshot.session_id == session_id, models.Snapshot.year == year)
    )
    if existing and replace:
        existing.state = state
    elif existing:
        return
    else:
        db.add(models.Snapshot(session_id=session_id, year=year, state=state))
