# Park-IoT API (FastAPI)

API de prototipo para gestión de parqueaderos: **parqueaderos, zonas, sensores, palancas, visitas** y un endpoint runtime para **capturar foto y leer placa** con OpenCV/ALPR desde cámaras locales o IP.

ESTA API NO ESTÁ TERMINADA AÚN, PERO SU FUNCIONALIDAD CORE Y ENDPOINTS FUNCIONAN.

## Stack
- Python 3.11+ (recomendado 3.12)
- FastAPI + Uvicorn
- SQLModel / SQLAlchemy
- OpenCV / OCR

## Requisitos
- Python 3.11+ instalado
- (Windows, si usas webcam USB) Drivers OK y permisos para acceder a la cámara

## Recomendaciones
Para que no haya retraso de respuesta al usar el endpoint de cámara, se recomienda ejecutar vision/test.py 1 vez para que se instale el modelo. Ya después irá rápido. La IA de reconocimiento de placas aún no está afinada.


## Instalación rápida
```bash
git clone <URL_DEL_REPO>
cd Back

# Crear entorno
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
````

> Si usas variables de entorno (p. ej. `DATABASE_URL`), crea un archivo `.env` en la raíz.
> Si no defines nada, el proyecto suele usar SQLite local definido en `app/db.py`.

## Ejecución en desarrollo

```bash
uvicorn app.main:app --reload --workers 1
```

* La API quedará en: `http://127.0.0.1:8000`

## Documentación

* **Swagger UI (auto)**: `http://127.0.0.1:8000/docs`
* **ReDoc (auto)**: `http://127.0.0.1:8000/redoc`
* **Doc pública (producción)**: pendiente por subir


