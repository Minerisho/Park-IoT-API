# app/routers/parqueaderos.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlmodel import Session, select
from ..db import get_session
from ..models.parqueadero import Parqueadero
from ..models.zona import Zona
from ..models.visita import Visita
from ..models.palanca import Palanca
from ..core.enums import GateType
from ..models.sensor import Sensor
from ..schemas.parqueadero import (
    ParqueaderoCreate, ParqueaderoUpdate, ParqueaderoRead
)

router = APIRouter(prefix="/parqueaderos", tags=["parqueaderos"])

@router.post("", response_model=ParqueaderoRead, status_code=status.HTTP_201_CREATED)
def crear_parqueadero(json_body: ParqueaderoCreate, session: Session = Depends(get_session)):
    p = Parqueadero(**json_body.model_dump())
    session.add(p)
    session.commit()
    session.refresh(p)
    return p

@router.get("", response_model=list[ParqueaderoRead])
def listar_parqueaderos(
    limit: int | None = Query(default=None, ge=1, le=100),
    session: Session = Depends(get_session),
):
    q = select(Parqueadero).order_by(Parqueadero.id)
    rows = session.exec(q).all()
    return rows[:limit] if limit else rows

@router.get("/{parqueadero_id}", response_model=ParqueaderoRead)
def obtener_parqueadero(
    parqueadero_id: int = Path(ge=1),
    session: Session = Depends(get_session),
):
    p = session.get(Parqueadero, parqueadero_id)
    if not p:
        raise HTTPException(404, "Parqueadero no encontrado")
    return p

@router.patch("/{parqueadero_id}", response_model=ParqueaderoRead)
def actualizar_parqueadero(
    parqueadero_id: int,
    cambios: ParqueaderoUpdate,
    session: Session = Depends(get_session),
):
    p = session.get(Parqueadero, parqueadero_id)
    if not p:
        raise HTTPException(404, "Parqueadero no encontrado")
    data = cambios.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(p, k, v)
    session.add(p)
    session.commit()
    session.refresh(p)
    return p

@router.delete("/{parqueadero_id}", response_model=ParqueaderoRead)
def eliminar_parqueadero(
    parqueadero_id: int,
    session: Session = Depends(get_session),
):
    p = session.get(Parqueadero, parqueadero_id)
    if not p:
        raise HTTPException(404, "Parqueadero no encontrado")

    # ¿tiene zonas?
    tiene_zonas = session.exec(
        select(Zona.id).where(Zona.parqueadero_id == parqueadero_id)
    ).first() is not None

    # ¿tiene visitas?
    tiene_visitas = session.exec(
        select(Visita.id).where(Visita.parqueadero_id == parqueadero_id)
    ).first() is not None

    if tiene_zonas or tiene_visitas:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede borrar: tiene zonas/visitas asociadas",
        )

    session.delete(p)
    session.commit()
    return p

@router.get("/topologia")
def topologia(session: Session = Depends(get_session)):

    salida: dict = {}
    parques = session.exec(select(Parqueadero)).all()
    for p in parques:
        pal_in  = session.exec(select(Palanca).where(Palanca.parqueadero_id == p.id, Palanca.tipo == GateType.ENTRADA_PARQUEADERO)).first()
        pal_out = session.exec(select(Palanca).where(Palanca.parqueadero_id == p.id, Palanca.tipo == GateType.SALIDA_PARQUEADERO)).first()

        def sid(pal):
            if not pal: return None
            return session.exec(select(Sensor.id).where(Sensor.palanca_id == pal.id)).first()

        zonas_map = {}
        for z in session.exec(select(Zona).where(Zona.parqueadero_id == p.id)).all():
            z_pal = session.exec(select(Palanca).where(Palanca.zona_id == z.id, Palanca.tipo == GateType.ENTRADA_ZONA)).first()
            z_sid = session.exec(select(Sensor.id).where(Sensor.palanca_id == z_pal.id)).first() if z_pal else None
            if z_sid is None:
                z_sid = session.exec(select(Sensor.id).where(Sensor.zona_id == z.id)).first()
            zonas_map[z.nombre] = {
                "es_vip": z.es_vip,
                "capacidad": z.capacidad,
                "palanca": {"id": z_pal.id if z_pal else None, "sensor_id": z_sid}
            }

        salida[p.nombre] = {
            "id_parqueadero": p.id,
            "palanca_entrada": {"id": pal_in.id if pal_in else None, "sensor_id": sid(pal_in)},
            "palanca_salida":  {"id": pal_out.id if pal_out else None, "sensor_id": sid(pal_out)},
            "zonas": zonas_map
        }
    return salida