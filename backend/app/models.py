from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship

from .database import Base


class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True)
    block_no = Column(String, index=True)
    street = Column(String)
    postal_code = Column(String, index=True)
    units_1r = Column(Integer, default=0)
    units_2r = Column(Integer, default=0)
    units_3r = Column(Integer, default=0)
    units_4r = Column(Integer, default=0)
    units_5r = Column(Integer, default=0)
    lon = Column(Float)
    lat = Column(Float)
    height_m = Column(Float, default=30.0)
    footprint_area = Column(Float, default=400.0)

    @property
    def full_address(self) -> str:
        return f"Blk {self.block_no} {self.street}, Singapore {self.postal_code}"

    @property
    def total_units(self) -> int:
        return self.units_1r + self.units_2r + self.units_3r + self.units_4r + self.units_5r


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    current_year = Column(Integer, default=2025)
    status = Column(String, default="created")

    snapshots = relationship("Snapshot", back_populates="session", cascade="all, delete-orphan")
    movements = relationship("Movement", back_populates="session", cascade="all, delete-orphan")


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    year = Column(Integer, nullable=False)
    state = Column(JSON, nullable=False)

    session = relationship("Session", back_populates="snapshots")


Index("ix_snapshot_session_year", Snapshot.session_id, Snapshot.year, unique=True)


class Movement(Base):
    __tablename__ = "movements"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    year = Column(Integer, nullable=False)
    from_building_id = Column(Integer, ForeignKey("buildings.id"))
    to_building_id = Column(Integer, ForeignKey("buildings.id"))
    residents = Column(Integer, nullable=False)

    session = relationship("Session", back_populates="movements")


Index("ix_movement_session_year", Movement.session_id, Movement.year)
