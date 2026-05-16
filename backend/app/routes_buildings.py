from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import select

from . import models, schemas
from .database import get_db

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=list[schemas.BuildingOut])
def list_buildings(db: DBSession = Depends(get_db)):
    return db.scalars(select(models.Building)).all()


@router.get("/{building_id}", response_model=schemas.BuildingDetail)
def get_building(
    building_id: int,
    session_id: int | None = None,
    year: int | None = None,
    db: DBSession = Depends(get_db),
):
    b = db.get(models.Building, building_id)
    if not b:
        raise HTTPException(404, "Building not found")

    detail = schemas.BuildingDetail.model_validate(b).model_copy(update={
        "full_address": b.full_address,
        "total_units": b.total_units,
    })

    if session_id is not None:
        sess = db.get(models.Session, session_id)
        if not sess:
            raise HTTPException(404, "Session not found")
        target_year = year if year is not None else sess.current_year
        snap = db.scalar(
            select(models.Snapshot)
            .where(models.Snapshot.session_id == session_id, models.Snapshot.year == target_year)
        )
        if snap:
            occ = snap.state.get("occupancy", {}).get(str(building_id))
            if occ:
                detail = detail.model_copy(update={
                    "occupied_units_1r": occ.get("u1", 0),
                    "occupied_units_2r": occ.get("u2", 0),
                    "occupied_units_3r": occ.get("u3", 0),
                    "occupied_units_4r": occ.get("u4", 0),
                    "occupied_units_5r": occ.get("u5", 0),
                    "residents": occ.get("residents", 0),
                })
    return detail
