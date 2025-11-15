from sqlmodel import SQLModel, Field

class VehiculoVIP(SQLModel, table=True):
    __tablename__ = "vehiculos_vip"

    id: int | None = Field(default=None, primary_key=True)
    vehiculo_id: int = Field(foreign_key="vehiculos.id", index=True)
    parqueadero_id: int = Field(foreign_key="parqueaderos.id", index=True)
    activo: bool = True
