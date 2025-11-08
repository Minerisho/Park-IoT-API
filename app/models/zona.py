# app/models/zona.py
#from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from ..core._mixins import TimestampMixin
from sqlalchemy import UniqueConstraint
if TYPE_CHECKING:
    from .parqueadero import Parqueadero
    from .palanca import Palanca
    from .sensor import Sensor
    from .visita import Visita
    from .evento_zona import EventoZona

class Zona(TimestampMixin, SQLModel, table=True):
    
    __table_args__ = (
    UniqueConstraint("parqueadero_id", "orden", name="uq_zona_orden_por_parqueadero"),
    UniqueConstraint("parqueadero_id", "nombre", name="uq_zona_nombre_por_parqueadero"),
)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    parqueadero_id: int = Field(foreign_key="parqueadero.id", index=True)

    nombre: str = Field(min_length=1, max_length=60)
    es_vip: bool = Field(default=False)
    capacidad: int = Field(ge=0)
    conteo_actual: int = Field(default=0, ge=0)
    orden: int = Field(default=0)  
    
    parqueadero: "Parqueadero" = Relationship(back_populates="zonas")
    palanca_entrada: Optional["Palanca"] = Relationship(
        back_populates="zona",
        sa_relationship_kwargs={"uselist": False}
    )

    sensores: List["Sensor"] = Relationship(back_populates="zona")
    visitas: List["Visita"] = Relationship()
    eventos: List["EventoZona"] = Relationship(back_populates="zona")
