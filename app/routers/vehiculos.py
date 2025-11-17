from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlmodel import Session, select

from ..db import get_session
from ..models.vehiculo import Vehiculo
from ..schemas.vehiculo import VehiculoCreate, VehiculoRead, VehiculoUpdate

router = APIRouter(prefix="/vehiculos", tags=["vehiculos"])


def _normalize_placa(value: str) -> str:
    return value.strip().upper()


def _get_vehiculo_or_404(session: Session, vehiculo_id: int) -> Vehiculo:
    veh = session.get(Vehiculo, vehiculo_id)
    if not veh:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return veh


@router.post("", response_model=VehiculoRead, status_code=status.HTTP_201_CREATED)
def crear_vehiculo(body: VehiculoCreate, session: Session = Depends(get_session)):
    placa = _normalize_placa(body.placa)
    exists = session.exec(select(Vehiculo).where(Vehiculo.placa == placa)).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un vehículo con esa placa")
    veh = Vehiculo(
        placa=placa,
        activo=body.activo,
        en_lista_negra=body.en_lista_negra,
        vehiculo_vip=body.vehiculo_vip,
    )
    session.add(veh)
    session.commit()
    session.refresh(veh)
    return veh


@router.get("", response_model=list[VehiculoRead])
def listar_vehiculos(
    activo: bool | None = Query(default=None, description="Filtra por estado activo/inactivo"),
    en_lista_negra: bool | None = Query(
        default=None, description="Filtra por vehículos que están en la lista negra"
    ),
    vehiculo_vip: bool | None = Query(default=None, description="Filtra vehículos VIP"),
    session: Session = Depends(get_session),
):
    stmt = select(Vehiculo).order_by(Vehiculo.id)
    if activo is not None:
        stmt = stmt.where(Vehiculo.activo == activo)
    if en_lista_negra is not None:
        stmt = stmt.where(Vehiculo.en_lista_negra == en_lista_negra)
    if vehiculo_vip is not None:
        stmt = stmt.where(Vehiculo.vehiculo_vip == vehiculo_vip)
    return session.exec(stmt).all()


@router.get("/{vehiculo_id}", response_model=VehiculoRead)
def detalle_vehiculo(vehiculo_id: int = Path(ge=1), session: Session = Depends(get_session)):
    return _get_vehiculo_or_404(session, vehiculo_id)


@router.patch("/{vehiculo_id}", response_model=VehiculoRead)
def actualizar_vehiculo(
    vehiculo_id: int,
    cambios: VehiculoUpdate,
    session: Session = Depends(get_session),
):
    veh = _get_vehiculo_or_404(session, vehiculo_id)
    data = cambios.model_dump(exclude_unset=True)
    if "placa" in data and data["placa"] is not None:
        nueva_placa = _normalize_placa(data["placa"])
        conflicto = session.exec(select(Vehiculo).where(Vehiculo.placa == nueva_placa, Vehiculo.id != vehiculo_id)).first()
        if conflicto:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La placa ya está registrada")
        veh.placa = nueva_placa
    if "activo" in data and data["activo"] is not None:
        veh.activo = data["activo"]
    if "en_lista_negra" in data and data["en_lista_negra"] is not None:
        veh.en_lista_negra = data["en_lista_negra"]
    if "vehiculo_vip" in data and data["vehiculo_vip"] is not None:
        veh.vehiculo_vip = data["vehiculo_vip"]
    session.add(veh)
    session.commit()
    session.refresh(veh)
    return veh


@router.delete("/{vehiculo_id}", response_model=VehiculoRead)
def eliminar_vehiculo(vehiculo_id: int, session: Session = Depends(get_session)):
    veh = _get_vehiculo_or_404(session, vehiculo_id)
    session.delete(veh)
    session.commit()
    return veh