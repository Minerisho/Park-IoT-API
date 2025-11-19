# app/models/lectura_placa.py
#from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field


class LecturaPlaca(SQLModel, table=True):
    __tablename__ = "lecturas_placa"

    id: int = Field(default=None, primary_key=True)
    camara_id: int = Field(foreign_key="camaras.id", index=True)

    placa_detectada: str = Field(min_length=4, max_length=12)
    confianza: float = Field(ge=0.0, le=1.0)
    ruta_imagen: Optional[str] = Field(default=None, max_length=255)
    ruta_recorte: Optional[str] = Field(default=None, max_length=255)
    ts: datetime = Field(default_factory=datetime.now)

