# app/routers/parqueaderos.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlmodel import Session, select
from ..db import get_session
from ..models.parqueadero import Parqueadero
from ..models.zona import Zona
from ..models.visita import Visita
from ..models.palanca import Palanca
from ..core.enums import Type
from ..models.sensor import Sensor
from ..schemas.parqueadero import (
    ParqueaderoCreate, ParqueaderoUpdate, ParqueaderoRead
)

router = APIRouter(prefix="/parqueaderos", tags=["parqueaderos"])

@router.get("/topologia")
def topologia(session: Session = Depends(get_session)):
    salida: dict = {}
    parques = session.exec(select(Parqueadero)).all()

    for p in parques:
        pal_in  = session.exec(
            select(Palanca).where(
                Palanca.parqueadero_id == p.id,
                Palanca.tipo == Type.ENTRADA_PARQUEADERO
            )
        ).first()
        pal_out = session.exec(
            select(Palanca).where(
                Palanca.parqueadero_id == p.id,
                Palanca.tipo == Type.SALIDA_PARQUEADERO
            )
        ).first()

        def sid(pal):
            if not pal:
                return None
            return session.exec(select(Sensor.id).where(Sensor.palanca_id == pal.id)).first()

        zonas_map = {}
        for z in session.exec(select(Zona).where(Zona.parqueadero_id == p.id)).all():
            z_pal = session.exec(
                select(Palanca).where(
                    Palanca.zona_id == z.id,
                    Palanca.tipo == Type.ENTRADA_ZONA
                )
            ).first()
            z_sid = session.exec(select(Sensor.id).where(Sensor.palanca_id == z_pal.id)).first() if z_pal else None
            if z_sid is None:
                z_sid = session.exec(select(Sensor.id).where(Sensor.zona_id == z.id)).first()

            zonas_map[z.nombre] = {
                "es_vip": z.es_vip,
                "capacidad": z.capacidad,
                "conteo_actual": z.conteo_actual,  # útil para el front
                "palanca": {"id": z_pal.id if z_pal else None, "sensor_id": z_sid}
            }

        salida[p.nombre] = {
            "id_parqueadero": p.id,
            "palanca_entrada": {"id": pal_in.id if pal_in else None, "sensor_id": sid(pal_in)},
            "palanca_salida":  {"id": pal_out.id if pal_out else None, "sensor_id": sid(pal_out)},
            "zonas": zonas_map
        }
    return salida

@router.post("", response_model=ParqueaderoRead, status_code=status.HTTP_201_CREATED)
def crear_parqueadero(json_body: ParqueaderoCreate, session: Session = Depends(get_session)):
    p = Parqueadero(**json_body.model_dump())
    session.add(p)