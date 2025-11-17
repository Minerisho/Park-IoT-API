from typing import Optional
from pydantic import BaseModel

class BlackListCreate(BaseModel):
    vehiculo_id: int
    parqueadero_id: int
    motivo: Optional[str] = None

class BlackListPatch(BaseModel):
    parqueadero_id: Optional[int] = None
    vehiculo_id: Optional[int] = None
    motivo: Optional[str] = None

class BlackListRead(BaseModel):
    id: int
    vehiculo_id: int
    parqueadero_id: int
    motivo: Optional[str] = None
    class Config:
        from_attributes = True
