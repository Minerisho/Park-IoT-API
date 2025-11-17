# app/schemas/camara.py
from pydantic import BaseModel, Field
from typing import Optional
from .common import OrmRead


class CamaraCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    device_index: Optional[int] = None        # ej. 0 o 1
    ubicacion: Optional[str] = None           # ej. 'ENTRADA' | 'SALIDA'
    activo: bool = True


class CamaraUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    device_index: Optional[int] = None
    ubicacion: Optional[str] = None
    activo: Optional[bool] = None


class CamaraRead(OrmRead):
    id: int
    nombre: str
    device_index: Optional[int] = None
    ubicacion: Optional[str] = None
    activo: bool

