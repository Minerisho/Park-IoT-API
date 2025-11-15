from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ---------- Lectura ----------
class VisitaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehiculo_id: int
    parqueadero_id: int
    zona_id: Optional[int] = None
    ts_entrada: datetime
    ts_salida: Optional[datetime] = None


# ---------- Creación ----------
class VisitaCreate(BaseModel):
    """
    CRUD simple: crear una visita.
    - Enviar EITHER vehiculo_id OR placa. Si llega placa y no existe, se crea el vehículo.
    - Si no envías ts_entrada, se tomará el tiempo actual.
    """
    vehiculo_id: Optional[int] = None
    placa: Optional[str] = None
    parqueadero_id: int
    zona_id: Optional[int] = None
    ts_entrada: Optional[datetime] = None


# ---------- Actualización (PATCH) ----------
class VisitaUpdate(BaseModel):
    """
    Actualización parcial:
    - Puedes mover la visita a otra zona (zona_id).
    - Puedes cerrar la visita enviando ts_salida o cerrarla "ahora" con cerrar=True.
    - También puedes corregir ts_entrada o ts_salida si la ESP32 lo necesita.
    """
    zona_id: Optional[int] = None
    ts_entrada: Optional[datetime] = None
    ts_salida: Optional[datetime] = None
    cerrar: Optional[bool] = None  # si True y ts_salida no viene, se usa "ahora"
