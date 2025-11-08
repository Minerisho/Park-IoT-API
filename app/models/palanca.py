# app/models/palanca.py
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlmodel import SQLModel, Field, Relationship
from ..core.enums import GateType, GateState

if TYPE_CHECKING:
    from .zona import Zona
    from .parqueadero import Parqueadero
    from .evento_parqueadero import EventoParqueadero
    from .sensor import Sensor

class Palanca(SQLModel, table=True):
    __table_args__ = (
        # Unicidad por ámbito:
        UniqueConstraint("parqueadero_id", "tipo", name="uq_palanca_parqueadero_tipo"),
        UniqueConstraint("zona_id", "tipo", name="uq_palanca_zona_tipo"),
        # Dueño XOR: o parqueadero o zona (no ambos, no ninguno)
        CheckConstraint(
            "(parqueadero_id IS NOT NULL AND zona_id IS NULL) OR "
            "(parqueadero_id IS NULL AND zona_id IS NOT NULL)",
            name="ck_palanca_duenio_xor"
        ),
        # Coherencia tipo ↔ dueño
        CheckConstraint(
            "(tipo IN ('ENTRADA_PARQUEADERO','SALIDA_PARQUEADERO') AND parqueadero_id IS NOT NULL AND zona_id IS NULL) OR "
            "(tipo = 'ENTRADA_ZONA' AND zona_id IS NOT NULL AND parqueadero_id IS NULL)",
            name="ck_palanca_tipo_duenio"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    parqueadero_id: Optional[int] = Field(default=None, foreign_key="parqueadero.id", index=True)
    zona_id: Optional[int] = Field(default=None, foreign_key="zona.id", index=True)

    tipo: GateType
    estado: GateState = Field(default=GateState.CERRADA)

    # Relaciones
    zona: Optional["Zona"] = Relationship(back_populates="palanca_entrada")
    parqueadero: Optional["Parqueadero"] = Relationship(back_populates="palancas")
    sensores: List["Sensor"] = Relationship(back_populates="palanca")

