from typing import Optional
from sqlmodel import SQLModel, Field


class Camara(SQLModel, table=True):
    __tablename__ = "camaras"  

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, min_length=1, max_length=100)

    
    device_index: Optional[int] = Field(
        default=None, description="Índice de dispositivo (ej. 0 o 1 en OpenCV)"
    )
    ubicacion: Optional[str] = Field(
        default=None, description="Etiqueta libre, p.ej. 'ENTRADA' o 'SALIDA'"
    )
    activo: bool = Field(default=True)
