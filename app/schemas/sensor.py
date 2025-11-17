from typing import Optional
from pydantic import BaseModel, field_validator
from ..core.enums import Type

class SensorCreate(BaseModel):
    tipo: Type
    nombre: str
    activo: bool = True
    zona_id: Optional[int] = None
    palanca_id: Optional[int] = None

    @field_validator("palanca_id")
    @classmethod
    def _al_menos_un_anclaje(cls, v, info):
        data = info.data
        if v is None and data.get("zona_id") is None:
            raise ValueError("Debes indicar al menos 'zona_id' o 'palanca_id'.")
        return v

class SensorUpdate(BaseModel):
    nombre: Optional[str] = None
    activo: Optional[bool] = None
    zona_id: Optional[int] = None
    palanca_id: Optional[int] = None
    # Nota: aquí permitimos dejar ambos en None (desanclar),
    # si no quieres permitirlo, valida igual que en Create.

class SensorRead(BaseModel):
    id: int
    tipo: Type
    nombre: str
    activo: bool
    zona_id: Optional[int]
    palanca_id: Optional[int]

    class Config:
        from_attributes = True