# app/routers/parqueaderos.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlmodel import Session, select
from ..db import get_session
from ..models.parqueadero import Parqueadero
from ..models.zona import Zona
from ..models.visita import Visita
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
