# app/schemas/camara.py
from pydantic import BaseModel, Field
from .common import OrmRead

class CamaraCreate(BaseModel):
    palanca_id: int
    rtsp_url: str = Field(min_length=3, max_length=200)

class CamaraUpdate(BaseModel):
    rtsp_url: str | None = Field(default=None, min_length=3, max_length=200)

class CamaraRead(OrmRead):
    id: int
    palanca_id: int
    rtsp_url: str
