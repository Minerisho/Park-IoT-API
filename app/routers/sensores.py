# app/routers/sensores.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from ..db import get_session
from ..models.sensor import Sensor
from ..models.zona import Zona
from ..models.palanca import Palanca
from ..models.evento_zona import EventoZona
from ..schemas.sensor import SensorCreate, SensorRead, SensorPatch, SensorTrigger, ConteoZona, TriggerBody
from ..core.enums import SensorType, EventType

router = APIRouter(prefix="/sensores", tags=["sensores"])

def _assert_owner_oneof(zona_id: int | None, palanca_id: int | None):
    has_z = zona_id is not None
    has_p = palanca_id is not None
    if has_z == has_p:
        raise HTTPException(422, "Debes especificar zona_id o palanca_id (uno, no ambos)")

def _assert_owner_exists(session: Session, zona_id: int | None, palanca_id: int | None):
    if zona_id is not None and session.get(Zona, zona_id) is None:
        raise HTTPException(404, "Zona no encontrada")
    if palanca_id is not None and session.get(Palanca, palanca_id) is None:
        raise HTTPException(404, "Palanca no encontrada")

def _assert_tipo_matches_owner(tipo: SensorType, zona_id: int | None, palanca_id: int | None):
    if tipo in (SensorType.ENTRADA_ZONA, SensorType.SALIDA_ZONA) and zona_id is None:
        raise HTTPException(422, f"{tipo.value} requiere zona_id (no palanca_id)")
    if tipo == SensorType.PRESENCIA_PALANCA and palanca_id is None:
        raise HTTPException(422, "PRESENCIA_PALANCA requiere palanca_id (no zona_id)")

def _assert_unico_por_ambito(session: Session, tipo: SensorType, zona_id: int | None, palanca_id: int | None):
    if zona_id is not None:
        exists = session.exec(
            select(Sensor.id).where(Sensor.zona_id == zona_id, Sensor.tipo == tipo)
        ).first()
        if exists is not None:
            raise HTTPException(409, "Ya existe un sensor de ese tipo para esta zona")
    if palanca_id is not None:
        exists = session.exec(
            select(Sensor.id).where(Sensor.palanca_id == palanca_id, Sensor.tipo == tipo)
        ).first()
        if exists is not None:
            raise HTTPException(409, "Ya existe un sensor de ese tipo para esta palanca")

@router.post("", response_model=SensorRead, status_code=status.HTTP_201_CREATED)
def crear_sensor(payload: SensorCreate, session: Session = Depends(get_session)):
    _assert_owner_oneof(payload.zona_id, payload.palanca_id)
    _assert_owner_exists(session, payload.zona_id, payload.palanca_id)
    _assert_tipo_matches_owner(payload.tipo, payload.zona_id, payload.palanca_id)
    _assert_unico_por_ambito(session, payload.tipo, payload.zona_id, payload.palanca_id)

    s = Sensor(**payload.model_dump())
    session.add(s)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Violación de unicidad al crear sensor")
    session.refresh(s)
    return s

@router.get("", response_model=list[SensorRead])
def listar_sensores(
    zona_id: int | None = Query(default=None),
    palanca_id: int | None = Query(default=None),
    tipo: SensorType | None = Query(default=None),
    session: Session = Depends(get_session),
):
    stmt = select(Sensor).order_by(Sensor.id)
    if zona_id is not None:
        stmt = stmt.where(Sensor.zona_id == zona_id)
    if palanca_id is not None:
        stmt = stmt.where(Sensor.palanca_id == palanca_id)
    if tipo is not None:
        stmt = stmt.where(Sensor.tipo == tipo)
    return session.exec(stmt).all()

@router.get("/{sensor_id}", response_model=SensorRead)
def detalle_sensor(sensor_id: int = Path(ge=1), session: Session = Depends(get_session)):
    s = session.get(Sensor, sensor_id)
    if not s:
        raise HTTPException(404, "Sensor no encontrado")
    return s

@router.patch("/{sensor_id}", response_model=SensorRead)
def actualizar_sensor(
    sensor_id: int = Path(ge=1),
    cambios: SensorPatch | None = None,
    session: Session = Depends(get_session),
):
    s = session.get(Sensor, sensor_id)
    if not s:
        raise HTTPException(404, "Sensor no encontrado")

    data = (cambios or SensorPatch()).model_dump(exclude_unset=True)
    if "nombre" in data:
        s.nombre = data["nombre"]
    if "activo" in data:
        s.activo = data["activo"]

    session.add(s)
    session.commit()
    session.refresh(s)
    return s

@router.delete("/{sensor_id}", response_model=SensorRead)
def eliminar_sensor(sensor_id: int = Path(ge=1), session: Session = Depends(get_session)):
    s = session.get(Sensor, sensor_id)
    if not s:
        raise HTTPException(404, "Sensor no encontrado")

    resp = SensorRead.model_validate(s, from_attributes=True)
    session.delete(s)
    session.commit()
    return resp

@router.post("/{sensor_id}/trigger", response_model=ConteoZona, status_code=status.HTTP_200_OK)
def trigger_sensor(
    sensor_id: int = Path(ge=1),
    body: TriggerBody = ...,
    session: Session = Depends(get_session),
):
    """
    Recibe un 'evento' (ENTRADA o SALIDA) para un sensor de zona,
    aplica la lógica de conteo de la zona y registra el EventoZona.
    """
    # 1) Cargar sensor
    s = session.get(Sensor, sensor_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    if not s.activo:
        raise HTTPException(status_code=409, detail="Sensor inactivo")

    # 2) Debe ser un sensor asociado a zona
    if s.zona_id is None:
        raise HTTPException(status_code=409, detail="Este sensor no está asociado a una zona")

    # 3) Cargar zona
    zona = session.get(Zona, s.zona_id)
    if not zona:
        raise HTTPException(status_code=404, detail="Zona asociada no encontrada")

    # 4) Tomar conteo_antes
    conteo_antes = zona.conteo_actual

    # 5) Aplicar reglas
    if body.evento == EventType.ENTRADA:
        if zona.conteo_actual >= zona.capacidad:
            raise HTTPException(status_code=409, detail="Zona llena, no se puede incrementar conteo")
        zona.conteo_actual = zona.conteo_actual + 1

    elif body.evento == EventType.SALIDA:
        if zona.conteo_actual <= 0:
            raise HTTPException(status_code=409, detail="Conteo ya está en 0, no se puede decrementar")
        zona.conteo_actual = zona.conteo_actual - 1

    else:
        raise HTTPException(status_code=422, detail="Evento no soportado para zonas")

    # 6) Conteo después
    conteo_despues = zona.conteo_actual

    # 7) Persistir zona + evento dentro de la misma transacción
    ev = EventoZona(
        zona_id=zona.id,
        sensor_id=s.id,
        tipo=body.evento,
        conteo_antes=conteo_antes,
        conteo_despues=conteo_despues,
        nota=body.nota,
    )
    session.add(zona)
    session.add(ev)
    session.commit()
    session.refresh(zona)
    # (si quieres el id del evento, también podrías hacer session.refresh(ev))

    # 8) Respuesta compacta para el dashboard (misma forma que ya usabas)
    return ConteoZona(
        zona_id=zona.id,
        evento=body.evento,
        conteo_actual=zona.conteo_actual,
        capacidad=zona.capacidad,
    )