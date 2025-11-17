"""Pruebas funcionales de eliminación (DELETE) para Park-IoT API."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import requests

CACHE_FILE = Path(__file__).with_name(".functional_test_cache.json")


def _build_url(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    return f"{base}{path}"


def _expect_status(resp: requests.Response, expected_status: int) -> Dict[str, Any]:
    if resp.status_code != expected_status:
        raise SystemExit(
            f"Error {resp.status_code} en {resp.request.method} {resp.request.url}: {resp.text}"
        )
    if resp.status_code == 204 or not resp.content:
        return {}
    if "application/json" in resp.headers.get("content-type", "").lower():
        return resp.json()
    return {}


def _load_cache() -> dict[str, Any]:
    if not CACHE_FILE.exists():
        raise SystemExit(
            f"No existe {CACHE_FILE}. Ejecuta primero post_functional_tests.py para generar datos."
        )
    return json.loads(CACHE_FILE.read_text())


def run_delete_tests(base_url: str, keep_cache: bool = False) -> None:
    cache = _load_cache()
    base_url = base_url or cache.get("base_url", "http://127.0.0.1:8000")
    session = requests.Session()

    visita_id = cache["visita"]["id"]
    print(f"Eliminando visita {visita_id}…")
    _expect_status(session.delete(_build_url(base_url, f"/visitas/{visita_id}")), 204)
    print("✓ Visita eliminada")

    palanca_id = cache["palanca"]["id"]
    print(f"Eliminando palanca {palanca_id}…")
    _expect_status(session.delete(_build_url(base_url, f"/palancas/{palanca_id}")), 200)
    print("✓ Palanca eliminada")

    zona_id = cache["zona"]["id"]
    print(f"Eliminando zona {zona_id}…")
    _expect_status(session.delete(_build_url(base_url, f"/zonas/{zona_id}")), 200)
    print("✓ Zona eliminada")

    parqueadero_id = cache["parqueadero"]["id"]
    print(f"Eliminando parqueadero {parqueadero_id}…")
    _expect_status(session.delete(_build_url(base_url, f"/parqueaderos/{parqueadero_id}")), 200)
    print("✓ Parqueadero eliminado")

    vehiculo_id = cache["vehiculo"]["id"]
    print(f"Eliminando vehículo {vehiculo_id}…")
    _expect_status(session.delete(_build_url(base_url, f"/vehiculos/{vehiculo_id}")), 200)
    print("✓ Vehículo eliminado")

    if not keep_cache and CACHE_FILE.exists():
        CACHE_FILE.unlink()
        print(f"Archivo {CACHE_FILE.name} eliminado.")
    elif keep_cache:
        print("Se conserva el archivo de cache por petición del usuario.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pruebas DELETE del Park-IoT API")
    parser.add_argument(
        "--base-url",
        default=None,
        help="URL base de la API (por defecto usa la almacenada en el cache de POST)",
    )
    parser.add_argument(
        "--keep-cache",
        action="store_true",
        help="Mantiene el archivo .functional_test_cache.json después de las eliminaciones",
    )
    args = parser.parse_args()

    run_delete_tests(args.base_url, keep_cache=args.keep_cache)


if __name__ == "__main__":
    main()