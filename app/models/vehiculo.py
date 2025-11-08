# app/models/vehiculo.py
#from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .visita import Visita
    from .vehiculo_vip import VehiculoVIP

class Vehiculo(SQLModel, table=True):
    __tablename__ = "vehiculos"

    id: Optional[int] = Field(default=None, primary_key=True)
    placa: str = Field(index=True, min_length=5, max_length=10)
    activo: bool = Field(default=True)
    # Relaciones
    visitas: List["Visita"] = Relationship(back_populates="vehiculo")
    vip_en: List["VehiculoVIP"] = Relationship(back_populates="vehiculo")
    
