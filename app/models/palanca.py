from sqlmodel import SQLModel, Field
from app.core.enums import GateType, GateState

class Palanca(SQLModel, table=True):
    __tablename__ = "palancas"

    id: int | None = Field(default=None, primary_key=True)
    tipo: GateType
    estado: GateState = GateState.CERRADA
    parqueadero_id: int | None = Field(default=None, foreign_key="parqueaderos.id", index=True)
    zona_id: int | None = Field(default=None, foreign_key="zonas.id", index=True)
