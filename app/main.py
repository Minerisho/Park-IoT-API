# app/main.py
from fastapi import FastAPI, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings, Settings
from .routers import parqueadero, zonas, palancas, sensores, visitas, black_list, camaras
from .db import create_db_and_tables
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()   # *** Inicialización de la BD ***
    yield

def create_app() -> FastAPI:
    cfg = get_settings()
    app = FastAPI(
        title=cfg.app_name,
        description=cfg.description,
        debug=cfg.debug,
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,          # luego lo restringimos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", status_code=status.HTTP_200_OK)
    def health():
        return {"status": "ok"}
    
    @app.get("/config")
    def show_config(setting:Settings = Depends(get_settings)):
        return {
            "app_name": setting.app_name,
            "debug": setting.debug,
            "db_url": setting.db_url,
            "cors_origins": setting.cors_origins
        }
        
    app.include_router(parqueadero.router)
    app.include_router(zonas.router)
    app.include_router(palancas.router)
    app.include_router(sensores.router)
    app.include_router(visitas.router)
    app.include_router(black_list.router)
    app.include_router(camaras.router)
    return app



app = create_app()
        
