from typing import Optional
from pydantic import BaseModel
from ..core.enums import GateType, GateState

class PalancaCreate(BaseModel):
    tipo: GateType
    parqueadero_id: Optional[int] = None
    zona_id: Optional[int] = None
    estado: GateState = GateState.CERRADA

class PalancaRead(BaseModel):
    id: int
    tipo: GateType
    estado: GateState
    parqueadero_id: Optional[int]
    zona_id: Optional[int]
    class Config: from_attributes = True

class PalancaSetEstadoBody(BaseModel):
    estado: GateState
    nota: Optional[str] = None  # solo informativa, no hay eventos
