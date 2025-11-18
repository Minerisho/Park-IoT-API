from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlmodel import Session, select
from ..db import get_session
from ..core.enums import Type
from ..models.palanca import Palanca
from ..models.zona import Zona
from ..models.parqueadero import Parqueadero
from ..schemas.palanca import PalancaCreate, PalancaRead, PalancaUpdate
from typing import Optional


router = APIRouter(prefix="/palancas", tags=["palancas"])

# ---------------------------
# Helpers
# ---------------------------
def _assert_fk_exist(session: Session, zona_id: Optional[int], parqueadero_id: Optional[int]) -> None:
    if zona_id is not None and session.get(Zona, zona_id) is None:
        raise HTTPException(status_code=422, detail="La zona indicada no existe.")
    if parqueadero_id is not None and session.get(Parqueadero, parqueadero_id) is None:
        raise HTTPException(status_code=422, detail="El parqueadero indicado no existe.")

@router.post("", response_model=PalancaRead, status_code=status.HTTP_201_CREATED)
def crear_palanca(body: PalancaCreate, session: Session = Depends(get_session)):
    if body.tipo in {Type.ENTRADA_PARQUEADERO, Type.SALIDA_PARQUEADERO} and body.parqueadero_id is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Las palancas de parqueadero requieren el id del parqueadero",
        )
    if body.tipo in {Type.ENTRADA_ZONA, Type.SALIDA_ZONA} and body.zona_id is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Las palancas de zona requieren el id de la zona",
        )

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

@router.patch("/{palanca_id}", response_model=PalancaRead)
def set_estado(palanca_id: int, body: PalancaUpdate, session: Session = Depends(get_session)):
    p = session.get(Palanca, palanca_id)
    if not p:
        raise HTTPException(status_code=404, detail="Palanca no encontrada")

    # Validaciones de anclajes (si se envían)
    
    if body.zona_id is not None or body.parqueadero_id is not None:
        _assert_fk_exist(session, body.zona_id, body.parqueadero_id)

    # Aplicar cambios parciales
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(p, k, v)

    session.add(p)
    session.commit()
    session.refresh(p)
    return p

@router.delete("/{palanca_id}", response_model=PalancaRead)
def eliminar_palanca(palanca_id: int = Path(ge=1), session: Session = Depends(get_session)):
    p = session.get(Palanca, palanca_id)
    if not p:
        raise HTTPException(status_code=404, detail="Palanca no encontrada")
    session.delete(p)
    session.commit()
    return p