from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class VisitaRead(BaseModel):

    id: int
    vehiculo_id: int
    parqueadero_id: int
    ts_entrada: datetime
    ts_salida: datetime | None

class VisitaCreate(BaseModel):

    vehiculo_id: int
    parqueadero_id: int
    ts_entrada: Optional[datetime] = None


class VisitaUpdate(BaseModel):

    vehiculo_id: Optional[int] = None
    parqueadero_id: Optional[int] = None
    ts_entrada: Optional[datetime] = None
    ts_salida: Optional[datetime] = None
