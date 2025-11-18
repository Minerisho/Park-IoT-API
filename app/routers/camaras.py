# app/routers/camaras.py
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlmodel import Session, select

from ..db import get_session
from ..models.camara import Camara
from ..schemas.camara import CamaraCreate, CamaraUpdate, CamaraRead

from ..vision.plate_recognizer import ColombianPlateRecognizer

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
        # Nota: LIKE puede ser case-sensitive según el backend
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
@router.get("/{camara_id}/capturar")
def capturar_placeholder(
    camara_id: int = Path(ge=1),
    session: Session = Depends(get_session)
):
    """
    Captura placa, inserta el index de la cámara, devuelve la la placa en string, confidencia y ruta de la imagen.

    """
    cam = _get(session, camara_id) 

    recognizer = ColombianPlateRecognizer(
        output_dir="app/vision/capturas",
        min_confidence_ocr=0.7,
        use_gpu=False,
    )

    placa, confidencia, img_ruta = recognizer.capture_and_read_plate(cam.device_index)

    return {
        "camara_id": camara_id,
        "placa": placa,
        "confidencia": confidencia,
        "imagen_ruta": img_ruta,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }