#from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from ..core.enums import IncidentType

class Incidente(SQLModel, table=True):
    __tablename__ = "incidentes"

    id: Optional[int] = Field(default=None, primary_key=True)
    tipo: IncidentType

    visita_id: Optional[int] = Field(default=None, foreign_key="visitas.id", index=True)
    placa_detectada: Optional[str] = Field(default=None, max_length=12)
    descripcion: Optional[str] = Field(default=None, max_length=300)

    resuelto: bool = Field(default=False)
    resuelto_por: Optional[str] = None
    resuelto_ts: Optional[datetime] = None

    ts: datetime = Field(default_factory=datetime.now, index=True)
