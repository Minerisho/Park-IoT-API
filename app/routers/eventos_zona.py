# app/routers/eventos_zona.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select
from ..db import get_session
from ..models.evento_zona import EventoZona
from ..schemas.evento_zona import EventoZonaRead
from ..core.enums import EventType

router = APIRouter(prefix="/eventos-zona", tags=["eventos-zona"])

@router.get("", response_model=list[EventoZonaRead])
def listar_eventos_zona(
    zona_id: int = Query(..., ge=1, description="Zona a consultar"),
    tipo: EventType | None = Query(default=None),
    desde: str | None = Query(default=None, description="ISO 8601 (ej. 2025-11-08T00:00:00)"),
    hasta: str | None = Query(default=None, description="ISO 8601"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    stmt = select(EventoZona).where(EventoZona.zona_id == zona_id)

    if tipo is not None:
        stmt = stmt.where(EventoZona.tipo == tipo)

    # Parseo simple sin zonas horarias; si quieres TZ lo afinamos luego
    from datetime import datetime
    if desde is not None:
        try:
            dt = datetime.fromisoformat(desde)
        except ValueError:
            raise HTTPException(422, "Formato inválido en 'desde'")
        stmt = stmt.where(EventoZona.ts >= dt)

    if hasta is not None:
        try:
            dt = datetime.fromisoformat(hasta)
        except ValueError:
            raise HTTPException(422, "Formato inválido en 'hasta'")
        stmt = stmt.where(EventoZona.ts <= dt)

    stmt = stmt.order_by(EventoZona.ts.desc()).offset(offset).limit(limit)
    rows = session.exec(stmt).all()
    return [EventoZonaRead.model_validate(r, from_attributes=True) for r in rows]


@router.get("/{evento_id}", response_model=EventoZonaRead)
def detalle_evento_zona(
    evento_id: int = Path(ge=1),
    session: Session = Depends(get_session)
):
    ev = session.get(EventoZona, evento_id)
    if not ev:
        raise HTTPException(404, "Evento no encontrado")
    return EventoZonaRead.model_validate(ev, from_attributes=True)
