# app/models/lectura_placa.py
#from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
if TYPE_CHECKING:
    from .camara import Camara

class LecturaPlaca(SQLModel, table=True):
    __tablename__ = "lecturas_placa"

    id: Optional[int] = Field(default=None, primary_key=True)
    camara_id: int = Field(foreign_key="camara.id", index=True)

    placa_detectada: str = Field(min_length=4, max_length=12)
    confianza: float = Field(ge=0.0, le=1.0)
    imagen_path: Optional[str] = Field(default=None, max_length=255)

    ts: datetime = Field(default_factory=datetime.now)

    # Relaciones
    camara: "Camara" = Relationship()
