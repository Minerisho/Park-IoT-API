from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlmodel import Session, select
from ..db import get_session
from ..models.black_list import BlackList
from ..models.vehiculo import Vehiculo
from ..schemas.black_list import BlackListCreate, BlackListRead, BlackListPatch

router = APIRouter(prefix="/black-list", tags=["black-list"])

def _get_or_create_vehiculo(session: Session, placa: str) -> Vehiculo:
    p = placa.strip().upper()
    v = session.exec(select(Vehiculo).where(Vehiculo.placa == p)).first()
    if v: return v
    v = Vehiculo(placa=p, activo=True)
    session.add(v); session.commit(); session.refresh(v)
    return v

@router.post("", response_model=BlackListRead, status_code=status.HTTP_201_CREATED)
def crear_black(body: BlackListCreate, session: Session = Depends(get_session)):
    veh = _get_or_create_vehiculo(session, body.placa)
    # Evitar duplicados por (vehiculo, parqueadero)
    exists = session.exec(
        select(BlackList).where(
            BlackList.vehiculo_id == veh.id,
            BlackList.parqueadero_id == body.parqueadero_id
        )
    ).first()
    if exists:
        raise HTTPException(409, "Ya está en la lista negra de este parqueadero")

    bl = BlackList(
        vehiculo_id=veh.id,
        parqueadero_id=body.parqueadero_id,
        activo=body.activo,
        nota=body.nota,
    )
    session.add(bl); session.commit(); session.refresh(bl)
    return BlackListRead(
        id=bl.id, vehiculo_id=veh.id, parqueadero_id=bl.parqueadero_id,
        activo=bl.activo, nota=bl.nota, placa=veh.placa
    )

@router.get("", response_model=list[BlackListRead])
def listar_black(
    parqueadero_id: int | None = Query(default=None),
    placa: str | None = Query(default=None),
    activos: bool | None = Query(default=None),
    session: Session = Depends(get_session),
):
    stmt = select(BlackList).order_by(BlackList.id.desc())
    if parqueadero_id is not None:
        stmt = stmt.where(BlackList.parqueadero_id == parqueadero_id)
    if activos is True:
        stmt = stmt.where(BlackList.activo == True)
    if activos is False:
        stmt = stmt.where(BlackList.activo == False)

    filas = session.exec(stmt).all()
    out: list[BlackListRead] = []
    for bl in filas:
        veh = session.get(Vehiculo, bl.vehiculo_id)
        if placa and veh and veh.placa != placa.strip().upper():
            continue
        out.append(BlackListRead(
            id=bl.id, vehiculo_id=bl.vehiculo_id, parqueadero_id=bl.parqueadero_id,
            activo=bl.activo, nota=bl.nota, placa=veh.placa if veh else ""
        ))
    return out

@router.get("/{bl_id}", response_model=BlackListRead)
def detalle_black(bl_id: int = Path(ge=1), session: Session = Depends(get_session)):
    bl = session.get(BlackList, bl_id)
    if not bl:
        raise HTTPException(404, "No encontrado")
    veh = session.get(Vehiculo, bl.vehiculo_id)
    return BlackListRead(
        id=bl.id, vehiculo_id=bl.vehiculo_id, parqueadero_id=bl.parqueadero_id,
        activo=bl.activo, nota=bl.nota, placa=veh.placa if veh else ""
    )

@router.patch("/{bl_id}", response_model=BlackListRead)
def actualizar_black(
    bl_id: int = Path(ge=1),
    patch: BlackListPatch = None,
    session: Session = Depends(get_session),
):
    bl = session.get(BlackList, bl_id)
    if not bl:
        raise HTTPException(404, "No encontrado")
    data = (patch or BlackListPatch()).model_dump(exclude_unset=True)
    if "activo" in data: bl.activo = data["activo"]
    if "nota" in data: bl.nota = data["nota"]
    session.add(bl); session.commit(); session.refresh(bl)
    veh = session.get(Vehiculo, bl.vehiculo_id)
    return BlackListRead(
        id=bl.id, vehiculo_id=bl.vehiculo_id, parqueadero_id=bl.parqueadero_id,
        activo=bl.activo, nota=bl.nota, placa=veh.placa if veh else ""
    )

@router.delete("/{bl_id}", response_model=BlackListRead)
def eliminar_black(bl_id: int = Path(ge=1), session: Session = Depends(get_session)):
    bl = session.get(BlackList, bl_id)
    if not bl:
        raise HTTPException(404, "No encontrado")
    veh = session.get(Vehiculo, bl.vehiculo_id)
    resp = BlackListRead(
        id=bl.id, vehiculo_id=bl.vehiculo_id, parqueadero_id=bl.parqueadero_id,
        activo=bl.activo, nota=bl.nota, placa=veh.placa if veh else ""
    )
    session.delete(bl); session.commit()
    return resp
