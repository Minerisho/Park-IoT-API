# app/models/vehiculo_vip.py

from typing import Optional, TYPE_CHECKING
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .vehiculo import Vehiculo
    from .parqueadero import Parqueadero

class VehiculoVIP(SQLModel, table=True):
    __tablename__ = "vehiculos_vip"
    __table_args__ = (
        UniqueConstraint("vehiculo_id", "parqueadero_id", name="uq_vip_vehiculo_parqueadero"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    vehiculo_id: int = Field(foreign_key="vehiculos.id", index=True)
    parqueadero_id: int = Field(foreign_key="parqueadero.id", index=True)
    activo: bool = Field(default=True)
    
    vehiculo: "Vehiculo" = Relationship(back_populates="vip_en")
    parqueadero: "Parqueadero" = Relationship(back_populates="vehiculos_vip")
