# app/schemas/evento_parqueadero.py
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from ..core.enums import GateState

class EventoParqueaderoRead(BaseModel):
    id: int
    palanca_id: int
    estado: GateState
    ts: datetime
    vehiculo_id: Optional[int] = None
    lectura_placa_id: Optional[int] = None
