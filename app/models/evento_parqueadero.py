# app/models/evento_parqueadero.py
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from ..core.enums import GateState  # 👈 cambia a GateState

if TYPE_CHECKING:
    from .palanca import Palanca
    from .vehiculo import Vehiculo
    from .lectura_placa import LecturaPlaca

class EventoParqueadero(SQLModel, table=True):
    __tablename__ = "eventos_parqueadero"

    id: Optional[int] = Field(default=None, primary_key=True)
    palanca_id: int = Field(foreign_key="palanca.id", index=True)
    vehiculo_id: Optional[int] = Field(default=None, foreign_key="vehiculos.id", index=True)

    estado: GateState  # 👈 antes era tipo: EventType
    lectura_placa_id: Optional[int] = Field(default=None, foreign_key="lecturas_placa.id")
    nota: Optional[str] = Field(default=None, max_length=255)
    ts: datetime = Field(default_factory=datetime.now, index=True)

    palanca: "Palanca" = Relationship()
    vehiculo: Optional["Vehiculo"] = Relationship()
    lectura_placa: Optional["LecturaPlaca"] = Relationship()
