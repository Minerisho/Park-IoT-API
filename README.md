# Park-IoT API (FastAPI)

API de prototipo para gestión de parqueaderos: **parqueaderos, zonas, sensores, palancas, visitas** y un endpoint runtime para **capturar foto y leer placa** con OpenCV/ALPR desde cámaras locales o IP.

ESTA API NO ESTÁ TERMINADA AÚN, PERO SU FUNCIONALIDAD CORE Y ENDPOINTS FUNCIONAN.

## Stack
- Python 3.11+ (recomendado 3.12)
- FastAPI + Uvicorn
- SQLModel / SQLAlchemy
- OpenCV (para captura de cámara)
- (Opcional) OCR/ALPR que tú integres en `app/services/alpr_runtime.py`

## Requisitos
- Python 3.11+ instalado
- (Windows, si usas webcam USB) Drivers OK y permisos para acceder a la cámara

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

* Usa **1 worker** cuando accedas a **webcams USB** para evitar conflictos con el dispositivo.
* La API quedará en: `http://127.0.0.1:8000`

## Documentación

* **Swagger UI (auto)**: `http://127.0.0.1:8000/docs`
* **ReDoc (auto)**: `http://127.0.0.1:8000/redoc`
* **Doc pública (producción)**: pendiente por subir

## Endpoints útiles (vista rápida)

* `GET /health` — ping de vida
* `POST /parqueaderos` — crea parqueadero
* `POST /zonas` — crea zona (VIP o no)
* `POST /palancas` — crea palanca (ENTRADA_PARQUEADERO, SALIDA_PARQUEADERO, ENTRADA_ZONA)
* `POST /palancas/{id}/accion` — abrir/cerrar
* `POST /palancas/{id}/estado` — fijar estado exacto (y registra evento)
* `POST /sensores` + `POST /sensores/{id}/trigger` — simular entrada/salida de zona
* `POST /visitas/entrada` — registrar entrada (elige zona respetando VIP y cupos)
* `POST /visitas/salida` — cerrar visita y decrementar conteo
* `POST /camaras-runtime/{id}/snapshot-placa` — **captura un frame y devuelve la placa** (usa OpenCV + tu ALPR)

## Probar todo con el “smoke”

```bash
python tools/smoke_runner.py
```

Este script:

1. Crea parqueadero, zonas, palancas y sensores de prueba
2. Simula triggers de sensores
3. Abre/cierra palancas y lista eventos
4. Registra una visita de entrada y valida rechazos por cupo

## Notas sobre cámaras

* Si `Camara.endpoint` es `0` o `1`, se usará la webcam USB con OpenCV (en Windows se usa `CAP_DSHOW`).
* Si `Camara.endpoint` es una URL RTSP/HTTP, se abrirá el stream por red.
* El endpoint runtime captura **un único frame**, ejecuta tu ALPR en `app/services/alpr_runtime.py` y devuelve `{ placa, confianza }`.

