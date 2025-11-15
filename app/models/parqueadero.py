from sqlmodel import SQLModel, Field

class Parqueadero(SQLModel, table=True):
    __tablename__ = "parqueaderos"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    direccion: str | None = None
