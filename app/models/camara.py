# app/models/camara.py
#from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .palanca import Palanca


class Camara(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    palanca_id: int = Field(foreign_key="palanca.id", index=True)
    rtsp_url: str = Field(min_length=3, max_length=200)

    palanca: "Palanca" = Relationship()
