# app/models/vehiculo.py
from sqlmodel import SQLModel, Field

class Vehiculo(SQLModel, table=True):
    __tablename__ = "vehiculos"

    id: int = Field(default=None, primary_key=True)
    placa: str = Field(index=True, min_length=5, max_length=10)
    activo: bool = Field(default=True)
    en_lista_negra: bool = Field(default=False, description="Indica si el vehículo está bloqueado")
    vehiculo_vip: bool = Field(default=False, description="Indica si el vehículo tiene beneficios VIP")