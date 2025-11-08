# app/schemas/visita.py
from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class VisitaEntrada(BaseModel):
    placa: str = Field(min_length=3)
    parqueadero_id: int = Field(ge=1)
    zona_id: Optional[int] = Field(default=None, ge=1, description="Opcional. Si viene, se fuerza esa zona.")

class VisitaSalida(BaseModel):
    # Cerrar por id directo, o por placa+parqueadero_id
    visita_id: Optional[int] = Field(default=None, ge=1)
    placa: Optional[str] = None
    parqueadero_id: Optional[int] = Field(default=None, ge=1)

class VisitaRead(BaseModel):
    id: int
    vehiculo_id: int
    parqueadero_id: int
    zona_id: Optional[int] = None
    ts_entrada: datetime
    ts_salida: Optional[datetime] = None
