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
def list_blacklist(
    id: int | None = Query(
        None,
        description="ID de la entrada en la tabla blacklist"
    ),
    vehiculo_id: int | None = Query(
        None,
        description="ID del vehículo asociado"
    ),
    parqueadero_id: int | None = Query(
        None,
        description="ID del parqueadero asociado"
    ),
        placa: str | None = Query(
        None,
        description="Placa del vehículo asociado (ej. ABC123 o ABC-123)",
    ),
    session: Session = Depends(get_session),
):
    stmt = select(BlackList)

    if placa is not None:
        placa_normalizada = placa.strip().upper()

        stmt = (
            select(BlackList)
            .join(Vehiculo, BlackList.vehiculo_id == Vehiculo.id)
            .where(Vehiculo.placa == placa_normalizada)
        )

    if id is not None:
        stmt = stmt.where(BlackList.id == id)

    if vehiculo_id is not None:
        stmt = stmt.where(BlackList.vehiculo_id == vehiculo_id)

    if parqueadero_id is not None:
        stmt = stmt.where(BlackList.parqueadero_id == parqueadero_id)

    resultados = session.exec(stmt).all()

    if resultados is None:
        raise HTTPException(status_code=404, detail="No se encontraron resultados en la blacklist")
    
    return resultados


@router.patch("/{blacklist_id}", response_model=BlackListRead)
def patch_blacklist(
    blacklist_id: int,
    data: BlackListPatch,
    session: Session = Depends(get_session),
):
    # 1. Buscar la fila a actualizar
    db_obj = session.get(BlackList, blacklist_id)
    if db_obj is None:
        raise HTTPException(status_code=404, detail="BlackList no encontrada")

    # 2. Obtener solo los campos enviados en el PATCH
    update_data = data.dict(exclude_unset=True)
    # Nota: si envías {"motivo": null}, aquí vendrá {"motivo": None} y se pondrá a NULL.

    # 3. Aplicar cambios campo por campo
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    # 4. Guardar en la BD
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)

    # 5. Devolver el objeto actualizado (Pydantic usa from_attributes=True)
    return db_obj

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
