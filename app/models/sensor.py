# app/models/sensor.py
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlmodel import SQLModel, Field, Relationship
from ..core.enums import SensorType

if TYPE_CHECKING:
    from .zona import Zona
    from .palanca import Palanca
    from .evento_zona import EventoZona

class Sensor(SQLModel, table=True):
    __table_args__ = (
        # Unicidad por ámbito
        UniqueConstraint("zona_id", "tipo", name="uq_sensor_zona_tipo"),
        UniqueConstraint("palanca_id", "tipo", name="uq_sensor_palanca_tipo"),
        # Dueño XOR
        CheckConstraint(
            "(zona_id IS NOT NULL AND palanca_id IS NULL) OR "
            "(zona_id IS NULL AND palanca_id IS NOT NULL)",
            name="ck_sensor_duenio_xor"
        ),
        # Coherencia tipo ↔ dueño
        CheckConstraint(
            "(tipo IN ('ENTRADA_ZONA','SALIDA_ZONA') AND zona_id IS NOT NULL AND palanca_id IS NULL) OR "
            "(tipo = 'PRESENCIA_PALANCA' AND palanca_id IS NOT NULL AND zona_id IS NULL)",
            name="ck_sensor_tipo_duenio"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    tipo: SensorType
    nombre: Optional[str] = Field(default=None, max_length=60)
    activo: bool = Field(default=True)

    # dueño (XOR)
    zona_id: Optional[int] = Field(default=None, foreign_key="zona.id", index=True)
    palanca_id: Optional[int] = Field(default=None, foreign_key="palanca.id", index=True)

    # telemetría mínima (podrás ampliarlo luego)
    ultimo_estado: Optional[bool] = None
    ultima_lectura: Optional[datetime] = None

    # relaciones
    zona: Optional["Zona"] = Relationship(back_populates="sensores")
    palanca: Optional["Palanca"] = Relationship(back_populates="sensores")
    eventos: List["EventoZona"] = Relationship(back_populates="sensor")
