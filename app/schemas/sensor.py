# app/schemas/sensor.py
from typing import Optional
from pydantic import BaseModel, Field
from ..core.enums import SensorType, EventType

class SensorBase(BaseModel):
    tipo: SensorType
    nombre: Optional[str] = None
    activo: bool = True

class SensorCreate(SensorBase):
    zona_id: Optional[int] = None
    palanca_id: Optional[int] = None

class SensorRead(SensorBase):
    id: int
    zona_id: Optional[int] = None
    palanca_id: Optional[int] = None

class SensorPatch(BaseModel):
    nombre: Optional[str] = None
    activo: Optional[bool] = None
    # Si NO quieres permitir mover el dueño por PATCH, no incluyas zona_id/palanca_id aquí.

class SensorTrigger(BaseModel):
    evento: EventType = Field(description="ENTRADA o SALIDA")

class TriggerBody(BaseModel):
    evento: EventType
    nota: Optional[str] = None

class ConteoZona(BaseModel):
    zona_id: int = Field(ge=1)
    evento: EventType
    conteo_actual: int = Field(ge=0)
    capacidad: int = Field(ge=0)

