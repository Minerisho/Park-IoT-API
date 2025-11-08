#from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from ..core.enums import DeviceType
if TYPE_CHECKING:
    from .comando import Comando

class Dispositivo(SQLModel, table=True):
    __tablename__ = "dispositivos"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(min_length=1, max_length=60, index=True)
    tipo: DeviceType = Field(default=DeviceType.ESP32)
    api_key_hash: str = Field(min_length=10)
    last_seen: Optional[datetime] = None
    online: Optional[bool] = None

    # Relación de conveniencia: comandos enviados a este dispositivo
    comandos: List["Comando"] = Relationship(back_populates="dispositivo")
