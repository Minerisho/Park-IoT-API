# app/models/evento_zona.py
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Index
from sqlmodel import SQLModel, Field, Relationship
from ..core.enums import EventType

if TYPE_CHECKING:
    from .zona import Zona
    from .sensor import Sensor

class EventoZona(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    zona_id: int = Field(foreign_key="zona.id", index=True)
    sensor_id: Optional[int] = Field(default=None, foreign_key="sensor.id", index=True)

    tipo: EventType
    ts: datetime = Field(default_factory=datetime.now, index=True)

    conteo_antes: int
    conteo_despues: int

    nota: Optional[str] = Field(default=None, max_length=200)

    # Relaciones
    zona: "Zona" = Relationship(back_populates="eventos")
    sensor: Optional["Sensor"] = Relationship(back_populates="eventos")


# Índices compuestos útiles para consultas por rango
Index("ix_evento_zona__zona_ts", EventoZona.zona_id, EventoZona.ts)
Index("ix_evento_zona__zona_tipo_ts", EventoZona.zona_id, EventoZona.tipo, EventoZona.ts)
