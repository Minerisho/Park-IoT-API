from typing import Optional
from pydantic import BaseModel

class BlackListCreate(BaseModel):
    placa: str
    parqueadero_id: int
    activo: bool = True
    nota: Optional[str] = None

class BlackListPatch(BaseModel):
    activo: Optional[bool] = None
    nota: Optional[str] = None

class BlackListRead(BaseModel):
    id: int
    vehiculo_id: int
    parqueadero_id: int
    activo: bool
    nota: Optional[str] = None
    placa: str

    class Config:
        from_attributes = True
