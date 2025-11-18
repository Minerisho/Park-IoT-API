from typing import Optional
from pydantic import BaseModel
from ..core.enums import Type

class PalancaCreate(BaseModel):
    tipo: Type
    parqueadero_id: Optional[int] = None
    zona_id: Optional[int] = None
    abierto: bool = True
    

class PalancaRead(BaseModel):
    id: int
    tipo: Type
    parqueadero_id: Optional[int]
    zona_id: Optional[int]
    abierto: bool

    class Config:
        from_attributes = True

class PalancaUpdate(BaseModel):
    tipo: Type = None
    parqueadero_id: Optional[int] = None
    zona_id: Optional[int] = None
    abierto: bool = True
    