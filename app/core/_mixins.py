# app/models/_mixins.py
from typing import Optional
from datetime import datetime
from sqlmodel import Field

class TimestampMixin:
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: Optional[datetime] = Field(default=None)
