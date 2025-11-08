# app/routers/visitas.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlmodel import Session, select

from ..db import get_session

# === Modelos (ORM) ===
from ..models.visita import Visita as VisitaModel
from ..models.vehiculo import Vehiculo as VehiculoModel
from ..models.vehiculo_vip import VehiculoVIP as VehiculoVIPModel
from ..models.parqueadero import Parqueadero as ParqueaderoModel
from ..models.zona import Zona as ZonaModel

# === Schemas (Pydantic) ===
# Ajusta estos imports a tus nombres reales de schemas.
from ..schemas.visita import (
    VisitaEntrada,   # placa: str, parqueadero_id: int, zona_id: Optional[int] = None
    VisitaSalida,    # parqueadero_id: int, placa: Optional[str] = None, visita_id: Optional[int] = None
    VisitaRead,      # respuesta estándar
)

router = APIRouter(prefix="/visitas", tags=["visitas"])

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _get_parqueadero(session: Session, parqueadero_id: int) -> ParqueaderoModel:
    p = session.get(ParqueaderoModel, parqueadero_id)
    if not p:
        raise HTTPException(404, "Parqueadero no encontrado")
    return p

def _get_or_create_vehiculo(session: Session, placa: str) -> VehiculoModel:
    placa_norm = placa.strip().upper()
    v = session.exec(select(VehiculoModel).where(VehiculoModel.placa == placa_norm)).first()
    if v:
        return v
    v = VehiculoModel(placa=placa_norm, activo=True)
    session.add(v)
    session.commit()
    session.refresh(v)
    return v

def _vehiculo_es_vip(session: Session, vehiculo_id: int, parqueadero_id: int) -> bool:
    return session.exec(
        select(VehiculoVIPModel.id).where(
            VehiculoVIPModel.vehiculo_id == vehiculo_id,
            VehiculoVIPModel.parqueadero_id == parqueadero_id,
            VehiculoVIPModel.activo == True,
        )
    ).first() is not None

def _pick_zona_para_visita(
    session: Session,
    parqueadero_id: int,
    prefer_vip: bool,
    zona_id_forzada: Optional[int] = None,
) -> ZonaModel:
    """
    Si zona_id_forzada viene, valida que pertenezca al parqueadero y tenga cupo.
    Si no viene, intenta VIP si prefer_vip==True y hay cupo; si no, primera no-VIP con cupo por 'orden'.
    """
    if zona_id_forzada is not None:
        z = session.get(ZonaModel, zona_id_forzada)
        if not z or z.parqueadero_id != parqueadero_id:
            raise HTTPException(422, "La zona indicada no pertenece a este parqueadero")
        if z.conteo_actual >= z.capacidad:
            raise HTTPException(409, "Zona llena, no hay cupo")
        return z

    # Intentar VIP
    if prefer_vip:
        z_vip = session.exec(
            select(ZonaModel).where(
                ZonaModel.parqueadero_id == parqueadero_id,
                ZonaModel.es_vip == True,
            )
        ).first()
        if z_vip and z_vip.conteo_actual < z_vip.capacidad:
            return z_vip

    # Primera zona no-VIP con cupo, orden asc
    z_nvip = session.exec(
        select(ZonaModel)
        .where(
            ZonaModel.parqueadero_id == parqueadero_id,
            ZonaModel.es_vip == False,
            ZonaModel.conteo_actual < ZonaModel.capacidad,
        )
        .order_by(ZonaModel.orden.asc())
    ).first()

    if not z_nvip:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "No hay zonas con cupo disponible",
                "action": "DERIVAR_SALIDA"  # para que el front sepa qué hacer
            },
        )
    return z_nvip

def _incrementar_conteo_zona(session: Session, zona: ZonaModel):
    if zona.conteo_actual >= zona.capacidad:
        raise HTTPException(409, "Zona llena, no se puede ingresar")
    zona.conteo_actual += 1
    session.add(zona)

def _decrementar_conteo_zona(session: Session, zona: ZonaModel):
    if zona.conteo_actual <= 0:
        raise HTTPException(409, "Conteo ya está en 0, no se puede salir")
    zona.conteo_actual -= 1
    session.add(zona)

# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------
@router.post("/entrada", response_model=VisitaRead, status_code=status.HTTP_201_CREATED)
def registrar_entrada(payload: VisitaEntrada, session: Session = Depends(get_session)):
    """
    Crea (o reusa) vehículo por placa, elige zona (VIP si corresponde) y abre una visita activa.
    Incrementa el conteo de la zona.
    """
    # Validaciones básicas
    _get_parqueadero(session, payload.parqueadero_id)

    # Vehículo
    veh = _get_or_create_vehiculo(session, payload.placa)

    # ¿VIP en este parqueadero?
    es_vip = _vehiculo_es_vip(session, veh.id, payload.parqueadero_id)

    # Elegir zona (forzada o automática considerando VIP)
    zona = _pick_zona_para_visita(
        session=session,
        parqueadero_id=payload.parqueadero_id,
        prefer_vip=es_vip,
        zona_id_forzada=getattr(payload, "zona_id", None),
    )

    # Asegurar que no hay ya una visita activa para este vehículo en este parqueadero
    visita_activa = session.exec(
        select(VisitaModel).where(
            VisitaModel.vehiculo_id == veh.id,
            VisitaModel.parqueadero_id == payload.parqueadero_id,
            VisitaModel.ts_salida.is_(None),
        ).order_by(VisitaModel.ts_entrada.desc())
    ).first()
    if visita_activa:
        raise HTTPException(409, "Ya existe una visita activa para este vehículo en este parqueadero")

    # Crear visita + aumentar conteo
    _incrementar_conteo_zona(session, zona)

    visita = VisitaModel(
        vehiculo_id=veh.id,
        parqueadero_id=payload.parqueadero_id,
        zona_id=zona.id,
        ts_entrada=datetime.utcnow(),
        ts_salida=None,
        # agrega otros campos si tu modelo los tiene (ej. ticket, nota, etc.)
    )

    session.add(visita)
    session.commit()
    session.refresh(visita)

    # Responder con schema
    return VisitaRead.model_validate(visita, from_attributes=True)

@router.post("/salida", response_model=VisitaRead, status_code=status.HTTP_200_OK)
def registrar_salida(payload: VisitaSalida, session: Session = Depends(get_session)):
    """
    Cierra la última visita activa (por visita_id o por placa+parqueadero) y decrementa el conteo de la zona.
    """
    visita: Optional[VisitaModel] = None

    if getattr(payload, "visita_id", None) is not None:
        visita = session.get(VisitaModel, payload.visita_id)
        if not visita:
            raise HTTPException(404, "Visita no encontrada")
        if visita.ts_salida is not None:
            raise HTTPException(409, "La visita ya está cerrada")
    else:
        if not payload.placa:
            raise HTTPException(422, "Debes indicar 'visita_id' o 'placa'")
        if not payload.parqueadero_id:
            raise HTTPException(422, "Debes indicar 'parqueadero_id' al usar 'placa'")

        _get_parqueadero(session, payload.parqueadero_id)
        placa_norm = payload.placa.strip().upper()
        veh = session.exec(select(VehiculoModel).where(VehiculoModel.placa == placa_norm)).first()
        if not veh:
            raise HTTPException(404, "Vehículo no encontrado")

        visita = session.exec(
            select(VisitaModel).where(
                VisitaModel.vehiculo_id == veh.id,
                VisitaModel.parqueadero_id == payload.parqueadero_id,
                VisitaModel.ts_salida.is_(None),
            ).order_by(VisitaModel.ts_entrada.desc())
        ).first()
        if not visita:
            raise HTTPException(404, "No hay visita activa para ese vehículo en este parqueadero")

    # Cerrar visita + bajar conteo en su zona (si tiene)
    zona = session.get(ZonaModel, visita.zona_id) if visita.zona_id else None
    if zona:
        _decrementar_conteo_zona(session, zona)

    visita.ts_salida = datetime.utcnow()
    session.add(visita)
    session.commit()
    session.refresh(visita)

    return VisitaRead.model_validate(visita, from_attributes=True)

@router.get("", response_model=list[VisitaRead])
def listar_visitas(
    parqueadero_id: Optional[int] = Query(default=None),
    placa: Optional[str] = Query(default=None),
    activas: Optional[bool] = Query(default=None, description="True=solo abiertas, False=solo cerradas"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    stmt = select(VisitaModel).order_by(VisitaModel.id.desc())

    if parqueadero_id is not None:
        stmt = stmt.where(VisitaModel.parqueadero_id == parqueadero_id)

    if placa:
        stmt_placa = placa.strip().upper()
        # join simple por placa
        sub = select(VehiculoModel.id).where(VehiculoModel.placa == stmt_placa)
        v_id = session.exec(sub).first()
        if v_id is None:
            return []
        stmt = stmt.where(VisitaModel.vehiculo_id == v_id)

    if activas is True:
        stmt = stmt.where(VisitaModel.ts_salida.is_(None))
    elif activas is False:
        stmt = stmt.where(VisitaModel.ts_salida.is_not(None))

    stmt = stmt.offset(offset).limit(limit)
    filas = session.exec(stmt).all()
    return [VisitaRead.model_validate(x, from_attributes=True) for x in filas]

@router.get("/{visita_id}", response_model=VisitaRead)
def detalle_visita(
    visita_id: int = Path(ge=1),
    session: Session = Depends(get_session),
):
    v = session.get(VisitaModel, visita_id)
    if not v:
        raise HTTPException(404, "Visita no encontrada")
    return VisitaRead.model_validate(v, from_attributes=True)
