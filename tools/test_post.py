"""Ejecutor de pruebas funcionales con peticiones POST.

Genera un parqueadero totalmente poblado (palancas, sensores y tres zonas,
incluyendo una VIP) además de un vehículo y una visita. De esta manera la
respuesta de ``/parqueaderos/topologia`` queda libre de valores ``null`` y
los otros scripts (GET/PATCH y DELETE) tienen datos listos para ejercitar los
endpoints.
"""
from __future__ import annotations

import argparse
import json
import random
import string
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests

CACHE_FILE = Path(__file__).with_name(".functional_test_cache.json")
ZONAS_A_CREAR = 3
VIP_ZONE_INDEX = 0


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


def _crear_palanca(session: requests.Session, base_url: str, body: Dict[str, Any]) -> Dict[str, Any]:
    return _expect_status(
        session.post(_build_url(base_url, "/palancas"), json=body),
        201,
    )


def _crear_sensor(session: requests.Session, base_url: str, body: Dict[str, Any]) -> Dict[str, Any]:
    return _expect_status(
        session.post(_build_url(base_url, "/sensores"), json=body),
        201,
    )


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

    print("Creando palancas y sensores del parqueadero…")
    palanca_entrada = _crear_palanca(
        session,
        base_url,
        {
            "tipo": "ENTRADA_PARQUEADERO",
            "parqueadero_id": parqueadero["id"],
            "abierto": True,
        },
    )
    palanca_salida = _crear_palanca(
        session,
        base_url,
        {
            "tipo": "SALIDA_PARQUEADERO",
            "parqueadero_id": parqueadero["id"],
            "abierto": True,
        },
    )
    sensor_entrada = _crear_sensor(
        session,
        base_url,
        {
            "tipo": "ENTRADA_PARQUEADERO",
            "nombre": f"Sensor Entrada Parqueadero {suffix}",
            "palanca_id": palanca_entrada["id"],
        },
    )
    sensor_salida = _crear_sensor(
        session,
        base_url,
        {
            "tipo": "SALIDA_PARQUEADERO",
            "nombre": f"Sensor Salida Parqueadero {suffix}",
            "palanca_id": palanca_salida["id"],
        },
    )
    print(
        "✓ Palancas del parqueadero listas (entrada #{pin}, salida #{pout})".format(
            pin=palanca_entrada["id"], pout=palanca_salida["id"]
        )
    )

    print("Creando zonas (incluida una VIP) con sus sensores…")
    zonas_cache: List[Dict[str, Any]] = []
    for idx in range(ZONAS_A_CREAR):
        zona_body = {
            "parqueadero_id": parqueadero["id"],
            "nombre": f"Zona {idx + 1} {timestamp}",
            "es_vip": idx == VIP_ZONE_INDEX,
            "capacidad": 10 + idx * 5,
        }
        zona = _expect_status(
            session.post(_build_url(base_url, "/zonas"), json=zona_body),
            201,
        )
        zona_palanca = _crear_palanca(
            session,
            base_url,
            {
                "tipo": "ENTRADA_ZONA",
                "zona_id": zona["id"],
                "parqueadero_id": parqueadero["id"],
                "abierto": True,
            },
        )
        zona_sensor = _crear_sensor(
            session,
            base_url,
            {
                "tipo": "ENTRADA_ZONA",
                "nombre": f"Sensor Zona {idx + 1} {suffix}",
                "zona_id": zona["id"],
                "palanca_id": zona_palanca["id"],
            },
        )
        zonas_cache.append({"zona": zona, "palanca": zona_palanca, "sensor": zona_sensor})
    print(f"✓ {len(zonas_cache)} zonas creadas")

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
        "zonas": zonas_cache,
        "palancas_parqueadero": {
            "entrada": palanca_entrada,
            "salida": palanca_salida,
        },
        "sensores_parqueadero": {
            "entrada": sensor_entrada,
            "salida": sensor_salida,
        },
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