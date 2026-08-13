# backend/app/api/instruments.py
"""Instrument lookup API endpoints.
Provides read‑only access to the instrument lookup table.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.songs import Instrument
from app.schemas.lookups import InstrumentSummary

router = APIRouter(prefix="/instruments", tags=["instruments"])

@router.get("/", response_model=list[InstrumentSummary])
def list_instruments(db: Session = Depends(get_db)):
    """Return all instruments ordered by name."""
    return db.query(Instrument).order_by(Instrument.name.asc()).all()

@router.get("/{instrument_id}", response_model=InstrumentSummary)
def get_instrument(instrument_id: int, db: Session = Depends(get_db)):
    """Return a single instrument by its integer ID."""
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return instrument
