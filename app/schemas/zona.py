# app/schemas/zona.py
from pydantic import BaseModel, Field
from .common import OrmRead

class ZonaCreate(BaseModel):
    parqueadero_id: int
    nombre: str = Field(min_length=1, max_length=60)
    es_vip: bool = False
    capacidad: int = Field(ge=0)
    orden: int = Field(ge=0, default=0)

class ZonaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=60)
    es_vip: bool | None = None
    capacidad: int | None = Field(default=None, ge=0)
    orden: int | None = Field(default=None, ge=0)

class ZonaRead(OrmRead):
    id: int
    parqueadero_id: int
    nombre: str
    es_vip: bool
    capacidad: int
    conteo_actual: int
    orden: int
