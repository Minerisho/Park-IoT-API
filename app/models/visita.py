# app/models/visita.py
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .vehiculo import Vehiculo
    from .parqueadero import Parqueadero
    from .zona import Zona

class Visita(SQLModel, table=True):
    __tablename__ = "visitas"

    id: Optional[int] = Field(default=None, primary_key=True)
    vehiculo_id: int = Field(foreign_key="vehiculos.id", index=True)
    parqueadero_id: int = Field(foreign_key="parqueadero.id", index=True)
    zona_id: Optional[int] = Field(default=None, foreign_key="zona.id", index=True)

    ts_entrada: datetime = Field(default_factory=datetime.now, index=True)
    ts_salida: Optional[datetime] = Field(default=None, index=True)

    # Relaciones (opcionales si no usas lazy)
    vehiculo: "Vehiculo" = Relationship(back_populates="visitas")
    parqueadero: "Parqueadero" = Relationship(back_populates="visitas")
    zona: Optional["Zona"] = Relationship()
