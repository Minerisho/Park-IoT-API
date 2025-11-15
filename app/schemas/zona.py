from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ZonaCreate(BaseModel):
    parqueadero_id: int
    nombre: str
    es_vip: bool = False
    capacidad: int = Field(ge=0, default=0)

class ZonaPatch(BaseModel):
    # La ESP32/Front puede actualizar estos campos
    nombre: Optional[str] = None
    es_vip: Optional[bool] = None
    capacidad: Optional[int] = Field(default=None, ge=0)
    conteo_actual: Optional[int] = Field(default=None, ge=0)

    @field_validator("conteo_actual")
    @classmethod
    def _non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("conteo_actual no puede ser negativo")
        return v

class ZonaRead(BaseModel):
    id: int
    parqueadero_id: int
    nombre: str
    es_vip: bool
    capacidad: int
    conteo_actual: int

    class Config:
        from_attributes = True
