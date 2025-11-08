# app/schemas/vehiculo.py
from pydantic import BaseModel, Field
from .common import OrmRead

class VehiculoCreate(BaseModel):
    placa: str = Field(min_length=5, max_length=10)
    activo: bool = True

class VehiculoUpdate(BaseModel):
    placa: str | None = Field(default=None, min_length=5, max_length=10)
    activo: bool | None = None

class VehiculoRead(OrmRead):
    id: int
    placa: str
    activo: bool
