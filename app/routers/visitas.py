from datetime import datetime
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



def _ensure_fk_exists(session: Session, model, pk: int, not_found_msg: str) -> None:
    if session.get(model, pk) is None:
        raise HTTPException(status_code=404, detail=not_found_msg)


# ---------------------- Endpoints CRUD ----------------------
@router.post("", response_model=VisitaRead, status_code=status.HTTP_201_CREATED)
def crear_visita(payload: VisitaCreate, session: Session = Depends(get_session)):
    """
    Crea una visita.
    - Requiere parqueadero_i.
    - ts_entrada opcional (si no pones nada, se pone automatico el tiempo de ahora).
    """
    # Validación de FK parqueadero
    _ensure_fk_exists(session, Parqueadero, payload.parqueadero_id, "Parqueadero no encontrado")

    # Resolver vehículo
    vehiculo_id: int = payload.vehiculo_id

    _ensure_fk_exists(session, Vehiculo, vehiculo_id, "Vehículo no encontrado")

    if payload.ts_entrada is None:
        ts_entrada = datetime.now()
    else:
        ts_entrada = payload.ts_entrada

    visita = Visita(
        vehiculo_id=vehiculo_id,
        parqueadero_id=payload.parqueadero_id,
        ts_entrada=ts_entrada,
        ts_salida=None,
    )
    session.add(visita)
    session.commit()
    session.refresh(visita)
    return VisitaRead.model_validate(visita, from_attributes=True)


@router.get("", response_model=list[VisitaRead])
def listar_visitas(session: Session = Depends(get_session)) -> list[VisitaRead]:
    visitas = session.exec(select(Visita)).all()
    return visitas


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
    if payload.parqueadero_id is not None:
        _ensure_fk_exists(session, Parqueadero, payload.parqueadero_id, "Parqueadero no encontrado")
        v.parqueadero_id = payload.parqueadero_id

    if payload.vehiculo_id is not None:
        _ensure_fk_exists(session, Vehiculo, payload.vehiculo_id, "Zona no encontrada")
        v.vehiculo_id = payload.vehiculo_id

    if payload.ts_entrada is not None:
        v.ts_entrada = payload.ts_entrada

    if payload.ts_salida is not None:
        v.ts_salida = payload.ts_salida


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
