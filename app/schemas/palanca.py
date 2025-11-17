from typing import Optional
from pydantic import BaseModel
from ..core.enums import GateType

class PalancaCreate(BaseModel):
    tipo: GateType
    parqueadero_id: Optional[int] = None
    zona_id: Optional[int] = None
    abierto: bool = True
    

class PalancaRead(BaseModel):
    id: int
    tipo: GateType
    parqueadero_id: Optional[int]
    zona_id: Optional[int]
    class Config: from_attributes = True
    abierto: bool

class PalancaSetEstadoBody(BaseModel):
    abierto: bool
    nota: Optional[str] = None  # solo informativa, no hay eventos
