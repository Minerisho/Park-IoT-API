# app/schemas/parqueadero.py
from pydantic import BaseModel, Field
from .common import OrmRead

class ParqueaderoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    direccion: str | None = Field(default=None, max_length=160)

class ParqueaderoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=80)
    direccion: str | None = Field(default=None, max_length=160)

class ParqueaderoRead(OrmRead):
    id: int
    nombre: str
    direccion: str | None = None
