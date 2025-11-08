# app/schemas/palanca.py
from typing import Optional
from pydantic import BaseModel, Field
from ..core.enums import GateType, GateState

class PalancaBase(BaseModel):
    tipo: GateType
    estado: GateState = Field(default=GateState.CERRADA)

class PalancaCreate(PalancaBase):
    parqueadero_id: Optional[int] = None
    zona_id: Optional[int] = None

class PalancaRead(PalancaBase):
    id: int
    parqueadero_id: Optional[int] = None
    zona_id: Optional[int] = None

class PalancaAccion(BaseModel):
    accion: str = Field(description="ABRIR o CERRAR")
    
class PalancaPatch(BaseModel):
    # Todos opcionales; solo se aplican si vienen en el body
    tipo: Optional[GateType] = None
    estado: Optional[GateState] = None
    parqueadero_id: Optional[int] = None
    zona_id: Optional[int] = None

class PalancaSetEstadoBody(BaseModel):
    estado: GateState
    nota: Optional[str] = None  # se guardará en el evento
    
