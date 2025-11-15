from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlmodel import Session, select

from ..db import get_session

# Modelos (tablas simples, sin relationships)
from ..models.visita import Visita
from ..models.vehiculo import Vehiculo
from ..models.parqueadero import Parqueadero
from ..models.zona import Zona

# Schemas
from ..schemas.visita import VisitaCreate, VisitaUpdate, VisitaRead


router = APIRouter(prefix="/visitas", tags=["visitas"])


# ---------------------- Helpers internos ----------------------
def _utcnow() -> datetime:
    # UTC consistente para registros. Si prefieres naive, cambia a datetime.utcnow()
    return datetime.now(timezone.utc)


def _ensure_fk_exists(session: Session, model, pk: int, not_found_msg: str) -> None:
    if session.get(model, pk) is None:
        raise HTTPException(status_code=404, detail=not_found_msg)


def _get_or_create_vehiculo_by_placa(session: Session, placa: str) -> Vehiculo:
    placa_norm = placa.strip().upper()
    v = session.exec(select(Vehiculo).where(Vehiculo.placa == placa_norm)).first()
    if v:
        return v
    v = Vehiculo(placa=placa_norm, activo=True)
    session.add(v)
    session.commit()
    session.refresh(v)
    return v


# ---------------------- Endpoints CRUD ----------------------
@router.post("", response_model=VisitaRead, status_code=status.HTTP_201_CREATED)
def crear_visita(payload: VisitaCreate, session: Session = Depends(get_session)):
    """
    Crea una visita.
    - Requiere parqueadero_id.
    - Acepta vehiculo_id o placa (si llega placa, se crea el vehículo si no existe).
    - zona_id es opcional.
    - ts_entrada opcional (si no llega, se usa ahora en UTC).
    """
    # Validación de FK parqueadero
    _ensure_fk_exists(session, Parqueadero, payload.parqueadero_id, "Parqueadero no encontrado")

    # Resolver vehículo
    vehiculo_id: Optional[int] = payload.vehiculo_id
    if vehiculo_id is None:
        if not payload.placa:
            raise HTTPException(422, detail="Debes enviar 'vehiculo_id' o 'placa'")
        veh = _get_or_create_vehiculo_by_placa(session, payload.placa)
        vehiculo_id = veh.id
    else:
        _ensure_fk_exists(session, Vehiculo, vehiculo_id, "Vehículo no encontrado")

    # Validar zona si viene
    if payload.zona_id is not None:
        _ensure_fk_exists(session, Zona, payload.zona_id, "Zona no encontrada")

    visita = Visita(
        vehiculo_id=vehiculo_id,
        parqueadero_id=payload.parqueadero_id,
        zona_id=payload.zona_id,
        ts_entrada=payload.ts_entrada or _utcnow(),
        ts_salida=None,
    )
    session.add(visita)
    session.commit()
    session.refresh(visita)
    return VisitaRead.model_validate(visita, from_attributes=True)


@router.get("", response_model=list[VisitaRead])
def listar_visitas(
    parqueadero_id: Optional[int] = Query(default=None),
    vehiculo_id: Optional[int] = Query(default=None),
    placa: Optional[str] = Query(default=None),
    activas: Optional[bool] = Query(default=None, description="True=solo abiertas, False=solo cerradas"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    """
    Lista visitas con filtros básicos.
    """
    stmt = select(Visita).order_by(Visita.id.desc())

    if parqueadero_id is not None:
        stmt = stmt.where(Visita.parqueadero_id == parqueadero_id)

    if vehiculo_id is not None:
        stmt = stmt.where(Visita.vehiculo_id == vehiculo_id)

    if placa:
        v = session.exec(select(Vehiculo).where(Vehiculo.placa == placa.strip().upper())).first()
        if not v:
            return []
        stmt = stmt.where(Visita.vehiculo_id == v.id)

    if activas is True:
        stmt = stmt.where(Visita.ts_salida.is_(None))
    elif activas is False:
        stmt = stmt.where(Visita.ts_salida.is_not(None))

    stmt = stmt.offset(offset).limit(limit)
    filas = session.exec(stmt).all()
    return [VisitaRead.model_validate(x, from_attributes=True) for x in filas]


@router.get("/{visita_id}", response_model=VisitaRead)
def detalle_visita(
    visita_id: int = Path(ge=1),
    session: Session = Depends(get_session),
):
    v = session.get(Visita, visita_id)
    if not v:
        raise HTTPException(404, "Visita no encontrada")
    return VisitaRead.model_validate(v, from_attributes=True)


@router.patch("/{visita_id}", response_model=VisitaRead)
def actualizar_visita(
    visita_id: int = Path(ge=1),
    payload: VisitaUpdate = ...,
    session: Session = Depends(get_session),
):
    v = session.get(Visita, visita_id)
    if not v:
        raise HTTPException(404, "Visita no encontrada")

    # Actualizaciones parciales
    if payload.zona_id is not None:
        _ensure_fk_exists(session, Zona, payload.zona_id, "Zona no encontrada")
        v.zona_id = payload.zona_id

    if payload.ts_entrada is not None:
        v.ts_entrada = payload.ts_entrada

    if payload.ts_salida is not None:
        v.ts_salida = payload.ts_salida
    elif payload.cerrar is True:
        # Cerrar "ahora" si no se envió ts_salida
        v.ts_salida = _utcnow()

    session.add(v)
    session.commit()
    session.refresh(v)
    return VisitaRead.model_validate(v, from_attributes=True)


@router.delete("/{visita_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_visita(
    visita_id: int = Path(ge=1),
    session: Session = Depends(get_session),
):
    v = session.get(Visita, visita_id)
    if not v:
        raise HTTPException(404, "Visita no encontrada")
    session.delete(v)
    session.commit()
    return
