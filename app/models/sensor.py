from sqlmodel import SQLModel, Field
from app.core.enums import SensorType

class Sensor(SQLModel, table=True):
    __tablename__ = "sensores"

    id: int | None = Field(default=None, primary_key=True)
    tipo: SensorType
    nombre: str
    activo: bool = True
    zona_id: int | None = Field(default=None, foreign_key="zonas.id", index=True)
    palanca_id: int | None = Field(default=None, foreign_key="palancas.id", index=True)
