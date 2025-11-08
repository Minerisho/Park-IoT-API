# app/routers/palancas.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from ..db import get_session
from ..models.parqueadero import Parqueadero
from ..models.zona import Zona
from ..models.palanca import Palanca
from ..models.evento_parqueadero import EventoParqueadero
from ..schemas.palanca import PalancaCreate, PalancaRead, PalancaAccion, PalancaPatch, PalancaSetEstadoBody
from ..core.enums import GateType, GateState

router = APIRouter(prefix="/palancas", tags=["palancas"])

def _assert_owner_oneof(parqueadero_id: int | None, zona_id: int | None):
    # exactamente uno de los dos
    has_p = parqueadero_id is not None
    has_z = zona_id is not None
    if has_p == has_z:
        raise HTTPException(422, detail="Debes especificar parqueadero_id o zona_id (uno, no ambos)")

def _assert_owner_exists(session: Session, parqueadero_id: int | None, zona_id: int | None):
    if parqueadero_id is not None and session.get(Parqueadero, parqueadero_id) is None:
        raise HTTPException(404, "Parqueadero no encontrado")
    if zona_id is not None and session.get(Zona, zona_id) is None:
        raise HTTPException(404, "Zona no encontrada")

def _assert_tipo_matches_owner(tipo: GateType, parqueadero_id: int | None, zona_id: int | None):
    if tipo == GateType.ENTRADA_ZONA and zona_id is None:
        raise HTTPException(422, "ENTRADA_ZONA requiere zona_id (no parqueadero_id)")
    if tipo in (GateType.ENTRADA_PARQUEADERO, GateType.SALIDA_PARQUEADERO) and parqueadero_id is None:
        raise HTTPException(422, f"{tipo.value} requiere parqueadero_id (no zona_id)")

def _assert_unico_por_ambito(session: Session, tipo: GateType, parqueadero_id: int | None, zona_id: int | None):
    if parqueadero_id is not None:
        exists = session.exec(
            select(Palanca.id).where(Palanca.parqueadero_id == parqueadero_id, Palanca.tipo == tipo)
        ).first()
        if exists is not None:
            raise HTTPException(409, "Ya existe una palanca de ese tipo para este parqueadero")
    if zona_id is not None:
        exists = session.exec(
            select(Palanca.id).where(Palanca.zona_id == zona_id, Palanca.tipo == tipo)
        ).first()
        if exists is not None:
            raise HTTPException(409, "Ya existe una palanca de ese tipo para esa zona")

def _registrar_evento_parqueadero(
    session: Session,
    palanca: Palanca,
    estado: GateState,
    vehiculo_id: int | None = None,
    lectura_placa_id: int | None = None,
):
    ev = EventoParqueadero(
        palanca_id=palanca.id,
        estado=estado,
        vehiculo_id=vehiculo_id,
        lectura_placa_id=lectura_placa_id
    )
    session.add(ev)

@router.post("", response_model=PalancaRead, status_code=status.HTTP_201_CREATED)
def crear_palanca(payload: PalancaCreate, session: Session = Depends(get_session)):
    _assert_owner_oneof(payload.parqueadero_id, payload.zona_id)
    _assert_owner_exists(session, payload.parqueadero_id, payload.zona_id)
    _assert_tipo_matches_owner(payload.tipo, payload.parqueadero_id, payload.zona_id)
    _assert_unico_por_ambito(session, payload.tipo, payload.parqueadero_id, payload.zona_id)

    p = Palanca(**payload.model_dump())
    session.add(p)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # Por si lo pasa la carrera entre verificación/commit
        raise HTTPException(409, "Violación de unicidad: ya existe una palanca igual en este ámbito")
    session.refresh(p)
    return p

@router.get("", response_model=list[PalancaRead])
def listar_palancas(
    parqueadero_id: int | None = Query(default=None),
    zona_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
):
    stmt = select(Palanca).order_by(Palanca.id)
    if parqueadero_id is not None:
        stmt = stmt.where(Palanca.parqueadero_id == parqueadero_id)
    if zona_id is not None:
        stmt = stmt.where(Palanca.zona_id == zona_id)
    return session.exec(stmt).all()

@router.get("/{palanca_id}", response_model=PalancaRead)
def detalle_palanca(
    palanca_id: int = Path(ge=1),
    session: Session = Depends(get_session),
):
    p = session.get(Palanca, palanca_id)
    if not p:
        raise HTTPException(404, "Palanca no encontrada")
    return p

@router.post("/{palanca_id}/accion", response_model=PalancaRead)
def accionar_palanca(
    palanca_id: int = Path(ge=1),
    body: PalancaAccion | None = None,
    session: Session = Depends(get_session),
):
    p = session.get(Palanca, palanca_id)
    if not p:
        raise HTTPException(404, "Palanca no encontrada")
    if body is None or body.accion not in {"ABRIR", "CERRAR"}:
        raise HTTPException(422, "accion debe ser ABRIR o CERRAR")

    nuevo_estado = GateState.ABIERTA if body.accion == "ABRIR" else GateState.CERRADA
    p.estado = nuevo_estado
    session.add(p)
    _registrar_evento_parqueadero(session, p, nuevo_estado)
    session.commit()
    session.refresh(p)
    return p

@router.patch("/{palanca_id}", response_model=PalancaRead)
def actualizar_palanca(
    palanca_id: int = Path(ge=1),
    cambios: PalancaPatch = None,
    session: Session = Depends(get_session),
):
    """
    Actualización parcial:
    - Puede cambiar tipo, estado y/o el dueño (parqueadero_id XOR zona_id).
    - Valida XOR, existencia de dueño, coherencia tipo↔dueño y unicidad por ámbito.
    """
    p = session.get(Palanca, palanca_id)
    if not p:
        raise HTTPException(404, "Palanca no encontrada")

    data = (cambios or PalancaPatch()).model_dump(exclude_unset=True)

    # Valores resultantes (si no vienen, se conservan los actuales)
    tipo = data.get("tipo", p.tipo)
    estado = data.get("estado", p.estado)
    parqueadero_id = data.get("parqueadero_id", p.parqueadero_id)
    zona_id = data.get("zona_id", p.zona_id)

    # Validaciones de negocio
    _assert_owner_oneof(parqueadero_id, zona_id)
    _assert_owner_exists(session, parqueadero_id, zona_id)
    _assert_tipo_matches_owner(tipo, parqueadero_id, zona_id)

    # Unicidad en el nuevo ámbito (excluyendo esta misma palanca)
    if parqueadero_id is not None:
        dup = session.exec(
            select(Palanca.id).where(
                Palanca.parqueadero_id == parqueadero_id,
                Palanca.tipo == tipo,
                Palanca.id != p.id,
            )
        ).first()
        if dup is not None:
            raise HTTPException(409, "Ya existe una palanca de ese tipo para este parqueadero")
    if zona_id is not None:
        dup = session.exec(
            select(Palanca.id).where(
                Palanca.zona_id == zona_id,
                Palanca.tipo == tipo,
                Palanca.id != p.id,
            )
        ).first()
        if dup is not None:
            raise HTTPException(409, "Ya existe una palanca de ese tipo para esa zona")

    # Aplicar cambios
    p.tipo = tipo
    p.estado = estado
    p.parqueadero_id = parqueadero_id
    p.zona_id = zona_id

    session.add(p)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Violación de unicidad al actualizar")
    session.refresh(p)
    return p

@router.delete("/{palanca_id}", response_model=PalancaRead)
def eliminar_palanca(
    palanca_id: int = Path(ge=1),
    session: Session = Depends(get_session),
):
    """
    Elimina una palanca y devuelve el objeto borrado (200).
    OJO: si en el futuro hay FKs (eventos) sin ON DELETE SET NULL, la BD puede bloquear el delete.
    """
    p = session.get(Palanca, palanca_id)
    if not p:
        raise HTTPException(404, "Palanca no encontrada")

    # Capturamos una copia serializable ANTES de borrar
    resp = PalancaRead.model_validate(p, from_attributes=True)

    session.delete(p)
    session.commit()
    return resp


@router.post("/{palanca_id}/estado", response_model=PalancaRead)
def set_estado_palanca(
    palanca_id: int = Path(ge=1),
    body: PalancaSetEstadoBody = ...,
    session: Session = Depends(get_session),
):
    p = session.get(Palanca, palanca_id)
    if not p:
        raise HTTPException(404, "Palanca no encontrada")

    p.estado = body.estado
    session.add(p)
    _registrar_evento_parqueadero(session, p, body.estado)
    session.commit()
    session.refresh(p)
    return p


@router.post("/{palanca_id}/abrir", response_model=PalancaRead, status_code=status.HTTP_200_OK)
def abrir_palanca(
    palanca_id: int = Path(ge=1),
    session: Session = Depends(get_session),
):
    body = PalancaSetEstadoBody(estado=GateState.ABIERTA, nota="Comando abrir")
    return set_estado_palanca(palanca_id, body, session)


@router.post("/{palanca_id}/cerrar", response_model=PalancaRead, status_code=status.HTTP_200_OK)
def cerrar_palanca(
    palanca_id: int = Path(ge=1),
    session: Session = Depends(get_session),
):
    body = PalancaSetEstadoBody(estado=GateState.CERRADA, nota="Comando cerrar")
    return set_estado_palanca(palanca_id, body, session)