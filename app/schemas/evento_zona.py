# app/schemas/evento_zona.py
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from ..core.enums import EventType

class EventoZonaRead(BaseModel):
    id: int
    zona_id: int
    sensor_id: Optional[int] = None
    tipo: EventType
    ts: datetime
    conteo_antes: int
    conteo_despues: int
    nota: Optional[str] = None

class EventoZonaQuery(BaseModel):
    zona_id: int = Field(ge=1)
    tipo: Optional[EventType] = None
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
