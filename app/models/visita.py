from datetime import datetime
from sqlmodel import SQLModel, Field

class Visita(SQLModel, table=True):
    __tablename__ = "visitas"

    id: int | None = Field(default=None, primary_key=True)
    vehiculo_id: int = Field(foreign_key="vehiculos.id", index=True)
    parqueadero_id: int = Field(foreign_key="parqueaderos.id", index=True)
    ts_entrada: datetime
    ts_salida: datetime | None = None
