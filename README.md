# Park-IoT API (FastAPI)

API de prototipo para gestión de parqueaderos: **parqueaderos, zonas, sensores, palancas, visitas** y un endpoint para **capturar foto y leer placa** con OpenCV/OCR desde cámaras locales.

## Stack
- Python 3.11+ (recomendado 3.12)
- FastAPI + Uvicorn
- SQLModel / SQLAlchemy
- OpenCV / OCR

## Requisitos
- Python 3.11+ instalado
- (Windows, si usas webcam USB) Drivers OK y permisos para acceder a la cámara

## Instalación rápida
```bash
git clone https://github.com/Minerisho/Park-IoT-API
cd Park-IoT-API

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
uvicorn app.main:app
```

* La API quedará en: `http://127.0.0.1:8000`

## Documentación

* **Swagger UI (auto)**: `http://127.0.0.1:8000/docs`
* **ReDoc (auto)**: `http://127.0.0.1:8000/redoc`



