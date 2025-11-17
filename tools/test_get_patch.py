"""Pruebas funcionales orientadas a GET y PATCH para Park-IoT API.

Lee los IDs almacenados por ``post_functional_tests.py`` y valida que los
recursos puedan consultarse y actualizarse correctamente, incluyendo los
nuevos atributos ``en_lista_negra`` y ``vehiculo_vip`` del vehículo.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
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


def run_get_patch_tests(base_url: str) -> dict[str, Any]:
    cache = _load_cache()
    base_url = base_url or cache.get("base_url", "http://127.0.0.1:8000")
    session = requests.Session()

    print("Verificando /health…")
    health = _expect_status(session.get(_build_url(base_url, "/health")), 200)
    print(f"✓ API responde: {health}")

    vehiculo_id = cache["vehiculo"]["id"]
    print(f"Consultando vehículo {vehiculo_id}…")
    vehiculo = _expect_status(
        session.get(_build_url(base_url, f"/vehiculos/{vehiculo_id}")),
        200,
    )
    print(
        "✓ Vehículo obtenido: {placa} (activo={activo}, en_lista_negra={black}, vip={vip})".format(
            placa=vehiculo["placa"],
            activo=vehiculo["activo"],
            black=vehiculo["en_lista_negra"],
            vip=vehiculo["vehiculo_vip"],
        )
    )

    vehiculo_patch_body = {
        "activo": not vehiculo["activo"],
        "en_lista_negra": not vehiculo["en_lista_negra"],
        "vehiculo_vip": not vehiculo["vehiculo_vip"],
    }
    vehiculo_patched = _expect_status(
        session.patch(_build_url(base_url, f"/vehiculos/{vehiculo_id}"), json=vehiculo_patch_body),
        200,
    )
    print(
        "✓ Vehículo actualizado: activo={activo}, en_lista_negra={black}, vip={vip}".format(
            activo=vehiculo_patched["activo"],
            black=vehiculo_patched["en_lista_negra"],
            vip=vehiculo_patched["vehiculo_vip"],
        )
    )

    print("Verificando listados filtrados por en_lista_negra…")
    vehiculos_blacklist = _expect_status(
        session.get(_build_url(base_url, "/vehiculos?en_lista_negra=true")),
        200,
    )
    print(f"✓ {len(vehiculos_blacklist)} vehículo(s) marcados en lista negra")

    print("Verificando listados filtrados por vehiculo_vip…")
    vehiculos_vip = _expect_status(
        session.get(_build_url(base_url, "/vehiculos?vehiculo_vip=true")),
        200,
    )
    print(f"✓ {len(vehiculos_vip)} vehículo(s) marcados como VIP")

    parqueadero_id = cache["parqueadero"]["id"]
    print(f"Consultando parqueadero {parqueadero_id}…")
    parqueadero = _expect_status(
        session.get(_build_url(base_url, f"/parqueaderos/{parqueadero_id}")),
        200,
    )
    print(f"✓ Parqueadero obtenido: {parqueadero['nombre']}")

    print("Listando zonas del parqueadero…")
    zonas = _expect_status(
        session.get(_build_url(base_url, f"/zonas?parqueadero_id={parqueadero_id}")),
        200,
    )
    print(f"✓ {len(zonas)} zona(s) encontradas")

    zona_id = cache["zona"]["id"]
    print(f"Consultando zona {zona_id}…")
    zona = _expect_status(
        session.get(_build_url(base_url, f"/zonas/{zona_id}")),
        200,
    )
    print(f"✓ Zona obtenida: {zona['nombre']} (capacidad {zona['capacidad']})")

    print("Aplicando PATCH sobre zona…")
    zona_patch_body = {
        "nombre": f"{zona['nombre']} - PATCH",
        "capacidad": zona["capacidad"] + 5,
    }
    zona_patched = _expect_status(
        session.patch(_build_url(base_url, f"/zonas/{zona_id}"), json=zona_patch_body),
        200,
    )
    print(
        "✓ Zona actualizada: {nombre} con capacidad {capacidad}".format(
            nombre=zona_patched["nombre"], capacidad=zona_patched["capacidad"]
        )
    )

    print("Aplicando PATCH sobre parqueadero…")
    parqueadero_patch_body = {
        "nombre": f"{parqueadero['nombre']} - PATCH",
        "direccion": parqueadero.get("direccion") or "Dirección parcheada",
    }
    parqueadero_patched = _expect_status(
        session.patch(
            _build_url(base_url, f"/parqueaderos/{parqueadero_id}"),
            json=parqueadero_patch_body,
        ),
        200,
    )
    print(f"✓ Parqueadero actualizado: {parqueadero_patched['nombre']}")

    visita_id = cache["visita"]["id"]
    print(f"Consultando visita {visita_id}…")
    visita = _expect_status(
        session.get(_build_url(base_url, f"/visitas/{visita_id}")),
        200,
    )
    print(f"✓ Visita recuperada con ts_entrada {visita['ts_entrada']}")

    visita_patch_body = {"ts_salida": datetime.utcnow().isoformat()}
    visita_patched = _expect_status(
        session.patch(_build_url(base_url, f"/visitas/{visita_id}"), json=visita_patch_body),
        200,
    )
    print(f"✓ Visita actualizada con ts_salida {visita_patched['ts_salida']}")

    cache.update(
        {
            "base_url": base_url,
            "parqueadero": parqueadero_patched,
            "zona": zona_patched,
            "vehiculo": vehiculo_patched,
            "visita": visita_patched,
        }
    )
    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))
    print(f"Cambios guardados en {CACHE_FILE.name}.")
    return cache


def main() -> None:
    parser = argparse.ArgumentParser(description="Pruebas GET/PATCH del Park-IoT API")
    parser.add_argument(
        "--base-url",
        default=None,
        help="URL base de la API (por defecto usa la almacenada en el cache de POST)",
    )
    args = parser.parse_args()

    run_get_patch_tests(args.base_url)


if __name__ == "__main__":
    main()