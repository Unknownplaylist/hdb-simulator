import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from .config import settings

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/boundary")
def boundary_geojson():
    p = Path(settings.boundary_path)
    if not p.exists():
        raise HTTPException(503, f"Boundary GeoJSON not found at {p}.")
    with p.open() as f:
        return JSONResponse(json.load(f))
