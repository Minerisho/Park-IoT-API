from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlmodel import Session, select
from ..db import get_session
from ..models.palanca import Palanca
from ..schemas.palanca import PalancaCreate, PalancaRead, PalancaSetEstadoBody

router = APIRouter(prefix="/palancas", tags=["palancas"])

@router.post("", response_model=PalancaRead, status_code=status.HTTP_201_CREATED)
def crear_palanca(body: PalancaCreate, session: Session = Depends(get_session)):
    p = Palanca(**body.model_dump())
    session.add(p); session.commit(); session.refresh(p)
    return p

@router.get("", response_model=list[PalancaRead])
def listar_palancas(
    parqueadero_id: int | None = Query(default=None),
    zona_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
):
    stmt = select(Palanca).order_by(Palanca.id)
    if parqueadero_id is not None: stmt = stmt.where(Palanca.parqueadero_id == parqueadero_id)
    if zona_id is not None:        stmt = stmt.where(Palanca.zona_id == zona_id)
    return session.exec(stmt).all()

@router.get("/{palanca_id}", response_model=PalancaRead)
def detalle_palanca(palanca_id: int = Path(ge=1), session: Session = Depends(get_session)):
    p = session.get(Palanca, palanca_id)
    if not p: raise HTTPException(404, "Palanca no encontrada")
    return p

@router.patch("/{palanca_id}/estado", response_model=PalancaRead)
def set_estado(palanca_id: int, body: PalancaSetEstadoBody, session: Session = Depends(get_session)):
    p = session.get(Palanca, palanca_id)
    if not p: raise HTTPException(404, "Palanca no encontrada")
    p.abierto = body.abierto
    session.add(p); session.commit(); session.refresh(p)
    return p

@router.delete("/{palanca_id}", response_model=PalancaRead)
def eliminar_palanca(palanca_id: int, session: Session = Depends(get_session)):
    p = session.get(Palanca, palanca_id)
    if not p: raise HTTPException(404, "Palanca no encontrada")
    session.delete(p); session.commit()
    return p
