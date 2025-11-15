from sqlmodel import SQLModel, Field

class BlackList(SQLModel, table=True):
    __tablename__ = "black_list"

    id: int | None = Field(default=None, primary_key=True)
    vehiculo_id: int = Field(foreign_key="vehiculos.id", index=True)
    parqueadero_id: int = Field(foreign_key="parqueaderos.id", index=True)
    activo: bool = True
    motivo: str | None = None
