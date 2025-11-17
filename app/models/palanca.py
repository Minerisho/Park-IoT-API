from sqlmodel import SQLModel, Field
from app.core.enums import GateType

class Palanca(SQLModel, table=True):
    __tablename__ = "palancas"

    id: int | None = Field(default=None, primary_key=True)
    tipo: GateType = Field(index=True)
    abierto: bool = Field(default=True)
    parqueadero_id: int | None = Field(
        default=None, foreign_key="parqueaderos.id", index=True
    )
    zona_id: int | None = Field(default=None, foreign_key="zonas.id", index=True)