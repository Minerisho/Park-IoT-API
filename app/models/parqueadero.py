# app/models/parqueadero.py
#from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from ..core._mixins import TimestampMixin

if TYPE_CHECKING:
    from .visita import Visita
    from .zona import Zona
    from .vehiculo_vip import VehiculoVIP
    from .palanca import Palanca

class Parqueadero(TimestampMixin, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, min_length=1, max_length=80)
    direccion: Optional[str] = Field(default=None, max_length=160)

    zonas: List["Zona"] = Relationship(
        back_populates="parqueadero",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    
    vehiculos_vip: List["VehiculoVIP"] = Relationship(back_populates="parqueadero")
    
    visitas: List["Visita"] = Relationship(
        back_populates="parqueadero",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    
    palancas: list["Palanca"] = Relationship(back_populates="parqueadero")
    
