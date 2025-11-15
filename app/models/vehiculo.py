# app/models/vehiculo.py
from typing import Optional
from sqlmodel import SQLModel, Field

class Vehiculo(SQLModel, table=True):
    __tablename__ = "vehiculos"

    id: int = Field(default=None, primary_key=True)
    placa: str = Field(index=True, min_length=5, max_length=10)
    activo: bool = Field(default=True)

    
