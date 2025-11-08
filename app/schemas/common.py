# app/schemas/common.py
from pydantic import BaseModel, ConfigDict

class OrmRead(BaseModel):
    """Base para respuestas. Habilita ORM mode en Pydantic v2."""
    model_config = ConfigDict(from_attributes=True)
