# tools/smoke_runner.py
# Uso:
#   py tools/smoke_runner.py
#
# Requisitos:
#   - Uvicorn corriendo: uvicorn app.main:app --reload
#   - requests instalado (pip install requests)

import json
import random
import string
import sys
from typing import Any, Dict, Optional

import requests


BASE_URL = "http://127.0.0.1:8000"


def call(method: str, path: str, **kwargs) -> requests.Response:
    url = f"{BASE_URL}{path}"
    resp = requests.request(method, url, **kwargs)
    print(f"{method:4} {path} -> {resp.status_code}")
    if resp.status_code >= 400:
        try:
            print("Body:", resp.text)
        except Exception:
            pass
        resp.raise_for_status()
    return resp


def rand_suffix(n: int = 6) -> str:
    return "".join(random.choices(string.hexdigits.lower(), k=n))


def main():
    print("== Smoke Topología + Cámaras ==")
    print()

    # 0) Health
    call("GET", "/health")

    # 1) Crear parqueadero
    suf = rand_suffix()
    nombre_parq = f"Parqueadero Central {suf}"
    rp = call(
        "POST",
        "/parqueaderos",
        json={"nombre": nombre_parq, "direccion": "Cra 1 # 2-34"},
    )
    parqueadero = rp.json()
    p_id = parqueadero["id"]
    print("Parqueadero:", parqueadero)

    # 2) Crear zonas (VIP y B)
    rz1 = call(
        "POST",
        "/zonas",
        json={
            "parqueadero_id": p_id,
            "nombre": "VIP",
            "es_vip": True,
            "capacidad": 5,
            # conteo_actual arranca en 0 (por defecto del modelo)
        },
    ).json()
    print("Zona VIP:", rz1)

    rz2 = call(
        "POST",
        "/zonas",
        json={
            "parqueadero_id": p_id,
            "nombre": "B",
            "es_vip": False,
            "capacidad": 2,
        },
    ).json()
    print("Zona B:", rz2)

    z_id_b = rz2["id"]

    # 3) Palancas: entrada/salida parqueadero + entrada zona B
    rp_in = call(
        "POST",
        "/palancas",
        json={"tipo": "ENTRADA_PARQUEADERO", "parqueadero_id": p_id},
    ).json()
    print("Palanca entrada parqueadero:", rp_in)

    rp_out = call(
        "POST",
        "/palancas",
        json={"tipo": "SALIDA_PARQUEADERO", "parqueadero_id": p_id},
    ).json()
    print("Palanca salida parqueadero:", rp_out)

    rp_zb_in = call(
        "POST",
        "/palancas",
        json={"tipo": "ENTRADA_ZONA", "zona_id": z_id_b},
    ).json()
    print("Palanca entrada zona B:", rp_zb_in)

    # 4) Sensores asociados a palancas (para que /topologia muestre sensor_id)
    #    Nota: el tipo depende de tu Enum de SensorType.
    rs_pin = call(
        "POST",
        "/sensores",
        json={
            "tipo": "ENTRADA_PARQUEADERO",
            "nombre": f"IR IN PARK {suf}",
            "activo": True,
            "palanca_id": rp_in["id"],
        },
    ).json()
    print("Sensor palanca entrada parqueadero:", rs_pin)

    rs_pout = call(
        "POST",
        "/sensores",
        json={
            "tipo": "SALIDA_PARQUEADERO",
            "nombre": f"IR OUT PARK {suf}",
            "activo": True,
            "palanca_id": rp_out["id"],
        },
    ).json()
    print("Sensor palanca salida parqueadero:", rs_pout)

    rs_zb_in = call(
        "POST",
        "/sensores",
        json={
            "tipo": "ENTRADA_ZONA",
            "nombre": f"IR IN ZB {suf}",
            "activo": True,
            "zona_id": z_id_b,
            "palanca_id": rp_zb_in["id"],
        },
    ).json()
    print("Sensor palanca entrada zona B:", rs_zb_in)

    # 5) Cámaras: crear dos (entrada/salida) y probar captura (placeholder)
    rc_in = call(
        "POST",
        "/camaras",
        json={
            "nombre": f"Cam ENTRADA {suf}",
            "device_index": 0,
            "ubicacion": "ENTRADA",
            "activo": True,
        },
    ).json()
    print("Cámara entrada:", rc_in)

    rc_out = call(
        "POST",
        "/camaras",
        json={
            "nombre": f"Cam SALIDA {suf}",
            "device_index": 1,
            "ubicacion": "SALIDA",
            "activo": True,
        },
    ).json()
    print("Cámara salida:", rc_out)

    # Captura placeholder (simulada con mock_placa)
    cap1 = call(
        "GET",
        f"/camaras/{rc_in['id']}/capturar",
        params={"mock_placa": "AAA123"},
    ).json()
    print("Captura cámara ENTRADA:", cap1)

    cap2 = call(
        "GET",
        f"/camaras/{rc_out['id']}/capturar",
        params={"mock_placa": "BBB987"},
    ).json()
    print("Captura cámara SALIDA:", cap2)

    # 6) Ajustar conteo_actual de la zona B (PATCH simple) para ver reflejo en /topologia
    patch_zb = call(
        "PATCH",
        f"/zonas/{z_id_b}",
        json={"conteo_actual": 1},
    ).json()
    print("Zona B tras PATCH conteo_actual=1:", patch_zb)

    # 7) Topología
    topo = call("GET", "/topologia").json()
    print("== /topologia ==")
    print(json.dumps(topo, indent=2, ensure_ascii=False))

    print("Smoke OK ✅")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        # Propaga código de error como código de salida del script
        sys.exit(1)
