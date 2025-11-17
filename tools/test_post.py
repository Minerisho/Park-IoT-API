"""Ejecutor de pruebas funcionales con peticiones POST.

Crea un parqueadero, una zona, una palanca, un vehículo y una visita. El
vehículo queda registrado con los indicadores ``en_lista_negra`` y
``vehiculo_vip`` para que los otros scripts (GET/PATCH y DELETE) puedan
validar los nuevos atributos.
"""
from __future__ import annotations

import argparse
import json
import random
import string
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import requests

CACHE_FILE = Path(__file__).with_name(".functional_test_cache.json")


def _rand_suffix(length: int = 5) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


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


def run_post_tests(base_url: str) -> dict[str, Any]:
    session = requests.Session()
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    suffix = _rand_suffix()

    print("Creando parqueadero de prueba…")
    parqueadero_body = {
        "nombre": f"Test Parqueadero {suffix}",
        "direccion": f"Calle {random.randint(1, 100)} #{random.randint(1, 50)}",  # noqa: S311
    }
    parqueadero = _expect_status(
        session.post(_build_url(base_url, "/parqueaderos"), json=parqueadero_body),
        201,
    )
    print(f"✓ Parqueadero creado con id {parqueadero['id']}")

    print("Creando zona asociada…")
    zona_body = {
        "parqueadero_id": parqueadero["id"],
        "nombre": f"Zona Central {timestamp}",
        "es_vip": False,
        "capacidad": 10,
    }
    zona = _expect_status(
        session.post(_build_url(base_url, "/zonas"), json=zona_body),
        201,
    )
    print(f"✓ Zona creada con id {zona['id']}")

    print("Creando palanca de entrada de parqueadero…")
    palanca_body = {
        "tipo": "ENTRADA_PARQUEADERO",
        "parqueadero_id": parqueadero["id"],
        "abierto": True,
    }
    palanca = _expect_status(
        session.post(_build_url(base_url, "/palancas"), json=palanca_body),
        201,
    )
    print(f"✓ Palanca creada con id {palanca['id']}")

    print("Registrando vehículo…")
    vehiculo_body = {
        "placa": f"TEST{suffix}",
        "activo": True,
        "en_lista_negra": False,
        "vehiculo_vip": bool(random.getrandbits(1)),
    }
    vehiculo = _expect_status(
        session.post(_build_url(base_url, "/vehiculos"), json=vehiculo_body),
        201,
    )
    print(f"✓ Vehículo creado con id {vehiculo['id']} ({vehiculo['placa']})")

    print("Creando visita asociada…")
    visita_body = {
        "vehiculo_id": vehiculo["id"],
        "parqueadero_id": parqueadero["id"],
    }
    visita = _expect_status(
        session.post(_build_url(base_url, "/visitas"), json=visita_body),
        201,
    )
    print(f"✓ Visita creada con id {visita['id']}")

    payload = {
        "base_url": base_url,
        "parqueadero": parqueadero,
        "zona": zona,
        "palanca": palanca,
        "vehiculo": vehiculo,
        "visita": visita,
    }
    CACHE_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"IDs guardados en {CACHE_FILE.name}. Ahora puedes ejecutar los otros scripts.")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Pruebas funcionales POST del Park-IoT API")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="URL base de la API (por defecto: %(default)s)",
    )
    args = parser.parse_args()

    run_post_tests(args.base_url)


if __name__ == "__main__":
    main()