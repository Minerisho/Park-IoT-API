# app/schemas/vehiculo.py
from pydantic import BaseModel, Field
from .common import OrmRead

class VehiculoCreate(BaseModel):
    placa: str = Field(
        min_length=7,
        max_length=7,
        pattern=r"^[A-Z]{3}-\d{3}$",
        description="Placa colombiana tipo ABC-123 (tres letras mayúsculas, guion, tres dígitos)"
    )
    activo: bool = True
    en_lista_negra: bool = False
    vehiculo_vip: bool = False

class VehiculoUpdate(BaseModel):
    placa: str = Field(
        min_length=7,
        max_length=7,
        pattern=r"^[A-Z]{3}-\d{3}$",
        description="Placa colombiana tipo ABC-123 (tres letras mayúsculas, guion, tres dígitos)"
    )
    activo: bool | None = None
    en_lista_negra: bool | None = None
    vehiculo_vip: bool | None = None

class VehiculoRead(OrmRead):
    id: int
    placa: str
    activo: bool
    en_lista_negra: bool
    vehiculo_vip: bool