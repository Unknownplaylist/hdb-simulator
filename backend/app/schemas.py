from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BuildingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    block_no: str | None
    street: str | None
    postal_code: str | None
    units_1r: int
    units_2r: int
    units_3r: int
    units_4r: int
    units_5r: int
    lon: float
    lat: float
    height_m: float
    footprint_area: float


class SessionCreate(BaseModel):
    name: str


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    current_year: int
    status: str


class SnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    state: dict


class MovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    from_building_id: int | None
    to_building_id: int | None
    residents: int


class BuildingDetail(BuildingOut):
    full_address: str
    total_units: int
    occupied_units_1r: int = 0
    occupied_units_2r: int = 0
    occupied_units_3r: int = 0
    occupied_units_4r: int = 0
    occupied_units_5r: int = 0
    residents: int = 0
