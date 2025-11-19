# app/routers/camaras.py
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, Request
from sqlmodel import Session, select

from ..db import get_session
from ..models.camara import Camara
from ..models.lectura_placa import LecturaPlaca  # <--- [NUEVO IMPORT]
from ..schemas.camara import CamaraCreate, CamaraUpdate, CamaraRead

router = APIRouter(prefix="/camaras", tags=["camaras"])

def _get(session: Session, camara_id: int) -> Camara:
    c = session.get(Camara, camara_id)
    if not c:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    return c

# ---------------------- CRUD ----------------------
@router.post("", response_model=CamaraRead, status_code=status.HTTP_201_CREATED)
def crear_camara(payload: CamaraCreate, session: Session = Depends(get_session)):
    nueva = Camara(**payload.model_dump())
    session.add(nueva)
    session.commit()
    session.refresh(nueva)
    return CamaraRead.model_validate(nueva, from_attributes=True)


@router.get("", response_model=List[CamaraRead])
def listar_camaras(
    q: Optional[str] = Query(default=None, description="Filtro por nombre (contiene)"),
    activas: Optional[bool] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    stmt = select(Camara).order_by(Camara.id.desc())

    if q:
        stmt = stmt.where(Camara.nombre.contains(q))

    if activas is True:
        stmt = stmt.where(Camara.activo == True)
    elif activas is False:
        stmt = stmt.where(Camara.activo == False)

    stmt = stmt.offset(offset).limit(limit)
    filas = session.exec(stmt).all()
    return [CamaraRead.model_validate(x, from_attributes=True) for x in filas]


@router.get("/{camara_id}", response_model=CamaraRead)
def detalle_camara(
    camara_id: int = Path(ge=1),
    session: Session = Depends(get_session),
):
    c = _get(session, camara_id)
    return CamaraRead.model_validate(c, from_attributes=True)


@router.patch("/{camara_id}", response_model=CamaraRead)
def actualizar_camara(
    camara_id: int = Path(ge=1),
    payload: CamaraUpdate = ...,
    session: Session = Depends(get_session),
):
    c = _get(session, camara_id)

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(c, k, v)

    session.add(c)
    session.commit()
    session.refresh(c)
    return CamaraRead.model_validate(c, from_attributes=True)


@router.delete("/{camara_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_camara(
    camara_id: int = Path(ge=1),
    session: Session = Depends(get_session),
):
    c = _get(session, camara_id)
    session.delete(c)
    session.commit()
    return


# ---------------------- captura ----------------------
@router.post("/{id_camara}/capturar")
async def capturar_placa_camara(
    id_camara: int, 
    request: Request,                   # Necesario para acceder a la IA cargada en memoria
    session: Session = Depends(get_session) # Necesario para guardar en la BD
):
    """
    Captura foto, detecta placa con IA, guarda el resultado en la BD y devuelve el resultado.
    """
    print(f"Buscando cámara con id [{id_camara}] ...")
    c = _get(session, id_camara)
    lector = request.app.state.lector
    texto_placa, confianza, ruta_full, ruta_rec = lector.capturar_placa(c.device_index)
    
    if texto_placa == "ERR_CAM":
        raise HTTPException(status_code=500, detail=f"No se pudo conectar a la cámara {id_camara}")
    elif texto_placa == "ERR_FRAME":
        raise HTTPException(status_code=500, detail="La cámara no devolvió imagen")
    elif texto_placa == "NO DETECTADO":
        lectura_mala = LecturaPlaca(
        camara_id=id_camara,
        placa_detectada=texto_placa,
        ts=datetime.now(),
        confianza=confianza,
        ruta_imagen=ruta_full,        
        ruta_recorte=ruta_rec         
    )
    
        session.add(lectura_mala)
        session.commit()
        session.refresh(lectura_mala)
        raise HTTPException(status_code=500, detail="No se detectó una placa en la imagen o la placa detectada no contenía texto") 

    nueva_lectura = LecturaPlaca(
        camara_id=id_camara,
        placa_detectada=texto_placa,
        ts=datetime.now(),
        confianza=confianza,
        ruta_imagen=ruta_full,        # Guardamos la ruta de la foto completa
        ruta_recorte=ruta_rec         # Guardamos la ruta del recorte (opcional)
    )
    
    session.add(nueva_lectura)
    session.commit()
    session.refresh(nueva_lectura)
    
    # 5. Responder al cliente
    return texto_placa

#-----------    GET de LecturaPlaca     -----------

@router.get("/lecturas", response_model=List[LecturaPlaca])
async def obtener_historial_lecturas(
    session: Session = Depends(get_session),
    camara_id: Optional[int] = None,  # Filtro opcional por cámara
    offset: int = 0,                  # Paginación: saltar X registros
    limit: int = Query(default=50, le=100) # Paginación: límite por página (max 100)
):
    """
    Obtiene el historial de placas leídas. 
    Se puede filtrar por cámara y usar paginación.
    Ordenado por fecha descendente (más reciente primero).
    """

    query = select(LecturaPlaca)
    if camara_id:
        query = query.where(LecturaPlaca.camara_id == camara_id)
    query = query.order_by(LecturaPlaca.ts.desc()) 
    query = query.offset(offset).limit(limit)
    lecturas = session.exec(query).all()
    
    return lecturas