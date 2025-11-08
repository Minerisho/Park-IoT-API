#from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from ..core.enums import CommandType, CommandStatus

if TYPE_CHECKING:
    from .dispositivo import Dispositivo

class Comando(SQLModel, table=True):
    __tablename__ = "comandos"

    id: Optional[int] = Field(default=None, primary_key=True)
    dispositivo_id: int = Field(foreign_key="dispositivos.id", index=True)

    type: CommandType
    status: CommandStatus = Field(default=CommandStatus.PENDING)

    # En SQLite moderno hay soporte JSON; si tu build diera lata,
    # puedes cambiar a: payload: str = Field(default="{}")
    payload: dict = Field(sa_column=Column(JSON))

    queued_at: datetime = Field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    ack_at: Optional[datetime] = None

    dispositivo: "Dispositivo" = Relationship(back_populates="comandos")
