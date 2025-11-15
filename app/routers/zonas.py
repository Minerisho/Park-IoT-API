from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlmodel import Session, select
from ..db import get_session
from ..models.zona import Zona
from ..schemas.zona import ZonaCreate, ZonaRead, ZonaPatch

router = APIRouter(prefix="/zonas", tags=["zonas"])

@router.post("", response_model=ZonaRead, status_code=status.HTTP_201_CREATED)
def crear_zona(body: ZonaCreate, session: Session = Depends(get_session)):
    z = Zona(**body.model_dump(), conteo_actual=0)
    session.add(z)
    session.commit()
    session.refresh(z)
    return z

@router.get("", response_model=list[ZonaRead])
def listar_zonas(
    parqueadero_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
):
    stmt = select(Zona).order_by(Zona.id)
    if parqueadero_id is not None:
        stmt = stmt.where(Zona.parqueadero_id == parqueadero_id)
    return session.exec(stmt).all()

@router.get("/{zona_id}", response_model=ZonaRead)
def detalle_zona(zona_id: int = Path(ge=1), session: Session = Depends(get_session)):
    z = session.get(Zona, zona_id)
    if not z:
        raise HTTPException(404, "Zona no encontrada")
    return z

@router.patch("/{zona_id}", response_model=ZonaRead)
def actualizar_zona(
    zona_id: int = Path(ge=1),
    cambios: ZonaPatch = None,
    session: Session = Depends(get_session),
):
    z = session.get(Zona, zona_id)
    if not z:
        raise HTTPException(404, "Zona no encontrada")

    data = (cambios or ZonaPatch()).model_dump(exclude_unset=True)

    # Validación “conteo_actual <= capacidad”
    nueva_cap = data.get("capacidad", z.capacidad)
    nuevo_conteo = data.get("conteo_actual", z.conteo_actual)
    if nuevo_conteo is not None and nueva_cap is not None and nuevo_conteo > nueva_cap:
        raise HTTPException(422, "conteo_actual no puede superar la capacidad")

    # Aplicar cambios
    if "nombre" in data: z.nombre = data["nombre"]
    if "es_vip" in data: z.es_vip = data["es_vip"]
    if "capacidad" in data: z.capacidad = data["capacidad"]
    if "conteo_actual" in data: z.conteo_actual = data["conteo_actual"]

    session.add(z)
    session.commit()
    session.refresh(z)
    return z

@router.delete("/{zona_id}", response_model=ZonaRead)
def eliminar_zona(zona_id: int = Path(ge=1), session: Session = Depends(get_session)):
    z = session.get(Zona, zona_id)
    if not z:
        raise HTTPException(404, "Zona no encontrada")
    session.delete(z)
    session.commit()
    return z
