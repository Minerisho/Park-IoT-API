# app/db.py
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import event
from sqlalchemy.engine import Engine
from .config import get_settings
from .models import (
    Parqueadero, Zona, Palanca, Sensor,
    Vehiculo, Visita,
    LecturaPlaca,
    Incidente
    )# noqa

settings = get_settings()
engine = create_engine(settings.db_url, echo=settings.debug)

# SQLite: habilitar claves foráneas
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        pass

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session