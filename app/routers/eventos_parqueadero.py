# app/routers/eventos_parqueadero.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select
from ..db import get_session
from ..models.evento_parqueadero import EventoParqueadero
from ..core.enums import GateState
from ..schemas.evento_parqueadero import EventoParqueaderoRead

router = APIRouter(prefix="/eventos-parqueadero", tags=["eventos-parqueadero"])

@router.get("", response_model=list[EventoParqueaderoRead])
def listar_eventos_parqueadero(
    palanca_id: int | None = Query(default=None),
    estado: GateState | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    stmt = (
        select(EventoParqueadero)
        .order_by(EventoParqueadero.ts.desc(), EventoParqueadero.id.desc())
    )
    if palanca_id is not None:
        stmt = stmt.where(EventoParqueadero.palanca_id == palanca_id)
    if estado is not None:
        stmt = stmt.where(EventoParqueadero.estado == estado)

    return session.exec(stmt.offset(offset).limit(limit)).all()

@router.get("/{evento_id}", response_model=EventoParqueaderoRead)
def detalle_evento_parqueadero(
    evento_id: int = Path(ge=1),
    session: Session = Depends(get_session),
):
    ev = session.get(EventoParqueadero, evento_id)
    if not ev:
        raise HTTPException(404, "Evento no encontrado")
    return ev
