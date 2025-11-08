# app/routers/zonas.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlmodel import Session, select, desc, asc
from ..db import get_session
from ..models.zona import Zona
from ..models.parqueadero import Parqueadero
from ..schemas.zona import ZonaCreate, ZonaUpdate, ZonaRead

router = APIRouter(prefix="/zonas", tags=["zonas"])

# ---- helpers de validación de reglas de negocio ----

def _assert_parqueadero_existe(session: Session, parqueadero_id: int) -> None:
    if session.get(Parqueadero, parqueadero_id) is None:
        raise HTTPException(status_code=404, detail="Parqueadero no encontrado")

def _assert_unica_zona_vip(session: Session, parqueadero_id: int) -> None:
    # Solo una VIP por parqueadero
    exists = session.exec(
        select(Zona.id).where(Zona.parqueadero_id == parqueadero_id, Zona.es_vip == True)  # noqa: E712
    ).first()
    if exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una zona VIP para este parqueadero",
        )

def _assert_nombre_unico(session: Session, parqueadero_id: int, nombre: str) -> None:
    exists = session.exec(
        select(Zona.id).where(Zona.parqueadero_id == parqueadero_id, Zona.nombre == nombre)
    ).first()
    if exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una zona con ese nombre en este parqueadero",
        )

def _assert_orden_unico(session, parqueadero_id: int, orden: int, excluir_id: int | None = None):
    q = select(Zona.id).where(Zona.parqueadero_id == parqueadero_id, Zona.orden == orden)
    existente = session.exec(q).first()
    if existente is not None and existente != excluir_id:
        raise HTTPException(status_code=409, detail=f"Ya existe una zona con orden {orden} en este parqueadero")

# ---- endpoints CRUD ----

@router.post("", response_model=ZonaRead, status_code=status.HTTP_201_CREATED)
def crear_zona(json_body: ZonaCreate, session: Session = Depends(get_session)):
    """
    Crea una zona en un parqueadero:
      - Verifica que el parqueadero exista.
      - (Opcional) Fuerza unicidad de nombre por parqueadero.
      - (Opcional) Garantiza 1 sola VIP por parqueadero.
      - Inicializa conteo_actual si tu modelo lo define con default=0.
    """
    _assert_parqueadero_existe(session, json_body.parqueadero_id)
    _assert_nombre_unico(session, json_body.parqueadero_id, json_body.nombre)
    if getattr(json_body, "es_vip", False):
        _assert_unica_zona_vip(session, json_body.parqueadero_id)

    z = Zona(**json_body.model_dump())
    if z.es_vip:
        z.orden = 0
    else:
        if z.orden is None or z.orden < 1:
            raise HTTPException(status_code=422, detail="Las zonas NO VIP deben tener orden ≥ 1")
        
    _assert_orden_unico(session, z.parqueadero_id, z.orden)
    
    session.add(z)
    session.commit()
    session.refresh(z)
    return z

@router.get("", response_model=list[ZonaRead])
def listar_zonas(
    parqueadero_id: int | None = Query(default=None, description="Filtra por parqueadero"),
    limit: int | None = Query(default=None, ge=1, le=100, description="Límite de filas"),
    session: Session = Depends(get_session),
):
    """
    Lista zonas; si envías ?parqueadero_id=X, filtra. Soporta ?limit=
    """
    #stmt = select(Zona).order_by(Zona.id)
    stmt = select(Zona).order_by(Zona.es_vip.desc(), Zona.orden.asc(), Zona.id.asc())
    if parqueadero_id is not None:
        stmt = stmt.where(Zona.parqueadero_id == parqueadero_id)
    rows = session.exec(stmt).all()
    return rows[:limit] if limit else rows

@router.get("/{zona_id}", response_model=ZonaRead)
def obtener_zona(zona_id: int = Path(ge=1), session: Session = Depends(get_session)):
    z = session.get(Zona, zona_id)
    if not z:
        raise HTTPException(404, "Zona no encontrada")
    return z

@router.patch("/{zona_id}", response_model=ZonaRead)
def actualizar_zona(
    zona_id: int,
    cambios: ZonaUpdate,
    session: Session = Depends(get_session),
):
    """
    Actualiza nombre/capacidad/es_vip/orden (según tu schema).
    Reglas:
      - No permitir capacidad < conteo_actual.
      - Si se marca es_vip=True, validar que no exista otra VIP en el parqueadero.
      - Mantener nombre único por parqueadero.
    """
    z = session.get(Zona, zona_id)
    if not z:
        raise HTTPException(404, "Zona no encontrada")

    data = cambios.model_dump(exclude_unset=True)

    es_vip_nuevo = data.get("es_vip", z.es_vip)
    orden_nuevo = data.get("orden", z.orden)
    
    if es_vip_nuevo:
        orden_nuevo = 0
    else:
        if orden_nuevo is None or orden_nuevo < 1:
            raise HTTPException(status_code=422, detail="Las zonas NO VIP deben tener orden ≥ 1")
        
    # validar capacidad
    if "capacidad" in data and data["capacidad"] < (z.conteo_actual or 0):
        raise HTTPException(
            status_code=422,
            detail=f"No puedes poner capacidad {data['capacidad']} < conteo_actual {z.conteo_actual}",
        )

    # validar nombre único si cambia
    if "nombre" in data and data["nombre"] != z.nombre:
        _assert_nombre_unico(session, z.parqueadero_id, data["nombre"])

    # validar VIP única si cambia a True
    if "es_vip" in data and data["es_vip"] and not z.es_vip:
        _assert_unica_zona_vip(session, z.parqueadero_id)

    # Si la zona ya es VIP o se va a convertir en VIP, ignoramos 'orden' del patch
    if z.es_vip or data.get("es_vip") is True:
        data.pop("orden", None)

    _assert_orden_unico(session, z.parqueadero_id, orden_nuevo, excluir_id=z.id)
    
    for k, v in data.items():
        setattr(z, k, v)

    session.add(z)
    session.commit()
    session.refresh(z)
    return z

@router.delete("/{zona_id}", response_model=ZonaRead)
def eliminar_zona(zona_id: int, session: Session = Depends(get_session)):
    """
    Borra una zona. Según tu política:
      - Si hay historial dependiente (visitas), puedes bloquear (409) o permitir si
        configuraste cascade en las relaciones hijos (palancas/sensores).
      - Aquí hacemos una versión simple: permitir si no hay historial (puedes ampliar luego).
    """
    z = session.get(Zona, zona_id)
    if not z:
        raise HTTPException(404, "Zona no encontrada")

    session.delete(z)
    session.commit()
    return z
