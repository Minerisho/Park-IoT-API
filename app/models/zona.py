from sqlmodel import SQLModel, Field

class Zona(SQLModel, table=True):
    __tablename__ = "zonas"

    id: int | None = Field(default=None, primary_key=True)
    parqueadero_id: int = Field(foreign_key="parqueaderos.id", index=True)
    nombre: str
    es_vip: bool = False
    capacidad: int
    conteo_actual: int = 0
