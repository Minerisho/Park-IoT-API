from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy import or_
from sqlmodel import Session, select
from ..db import get_session

from ..models.sensor import Sensor
from ..models.zona import Zona
from ..models.palanca import Palanca
from ..core.enums import Type
from ..schemas.sensor import SensorCreate, SensorUpdate, SensorRead

router = APIRouter(prefix="/sensores", tags=["sensores"])

# ---------------------------
# Helpers
# ---------------------------
def _assert_fk_exist(session: Session, zona_id: Optional[int], palanca_id: Optional[int]) -> None:
    if zona_id is not None and session.get(Zona, zona_id) is None:
        raise HTTPException(status_code=422, detail="La zona indicada no existe.")
    if palanca_id is not None and session.get(Palanca, palanca_id) is None:
        raise HTTPException(status_code=422, detail="La palanca indicada no existe.")

# ---------------------------
# Endpoints
# ---------------------------
PARQUEADERO_TYPES = {Type.ENTRADA_PARQUEADERO, Type.SALIDA_PARQUEADERO}
ZONA_TYPES = {Type.ENTRADA_ZONA, Type.SALIDA_ZONA}


@router.post("", response_model=SensorRead, status_code=status.HTTP_201_CREATED)
def crear_sensor(body: SensorCreate, session: Session = Depends(get_session)):
    zona_id = body.zona_id
    palanca_id = body.palanca_id

    if body.tipo in PARQUEADERO_TYPES:
        if palanca_id is None:
            raise HTTPException(422, "Para tipo de parqueadero debes enviar 'palanca_id'")
        zona_id = None
    elif body.tipo in ZONA_TYPES:
        if zona_id is None:
            raise HTTPException(422, "Para tipo de zona debes enviar 'zona_id'")
    else:
        raise HTTPException(422, "Tipo de sensor no soportado")

    _assert_fk_exist(session, zona_id, palanca_id)

    data = body.model_dump()
    data["zona_id"] = zona_id
    data["palanca_id"] = palanca_id
    s = Sensor(**data)
    session.add(s)
    session.commit()
    session.refresh(s)
    return s

@router.get("", response_model=list[SensorRead])
def listar_sensores(
    parqueadero_id: Optional[int] = Query(default=None, description="Filtra sensores por parqueadero (vía zona o palanca)"),
    zona_id: Optional[int] = Query(default=None),
    palanca_id: Optional[int] = Query(default=None),
    tipo: Optional[Type] = Query(default=None),
    activo: Optional[bool] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    stmt = select(Sensor)

    # Filtros directos
    if zona_id is not None:
        stmt = stmt.where(Sensor.zona_id == zona_id)
    if palanca_id is not None:
        stmt = stmt.where(Sensor.palanca_id == palanca_id)
    if tipo is not None:
        stmt = stmt.where(Sensor.tipo == tipo)
    if activo is not None:
        stmt = stmt.where(Sensor.activo == activo)

    # Filtro por parqueadero (vía join externo a Zona y Palanca)
    if parqueadero_id is not None:
        stmt = (
            stmt
            .outerjoin(Zona, Sensor.zona_id == Zona.id)
            .outerjoin(Palanca, Sensor.palanca_id == Palanca.id)
            .where(or_(Zona.parqueadero_id == parqueadero_id, Palanca.parqueadero_id == parqueadero_id))
            .distinct()
        )

    stmt = stmt.offset(offset).limit(limit)
    return session.exec(stmt).all()

@router.get("/{sensor_id}", response_model=SensorRead)
def detalle_sensor(sensor_id: int = Path(ge=1), session: Session = Depends(get_session)):
    s = session.get(Sensor, sensor_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return s

@router.patch("/{sensor_id}", response_model=SensorRead)
def actualizar_sensor(sensor_id: int, body: SensorUpdate, session: Session = Depends(get_session)):
    s = session.get(Sensor, sensor_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    # Validaciones de anclajes (si se envían)
    if body.zona_id is not None or body.palanca_id is not None:
        _assert_fk_exist(session, body.zona_id, body.palanca_id)

    # Aplicar cambios parciales
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(s, k, v)

    session.add(s)
    session.commit()
    session.refresh(s)
    return s

@router.delete("/{sensor_id}", response_model=SensorRead)
def eliminar_sensor(sensor_id: int, session: Session = Depends(get_session)):
    s = session.get(Sensor, sensor_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    session.delete(s)
    session.commit()
    return s
