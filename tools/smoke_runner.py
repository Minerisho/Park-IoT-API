# test_endpoints.py
import requests

BASE_URL = "http://localhost:8000"  # Cambia esto si tu API está en otro host/puerto


def show_response(resp, expected_status: int | None = None):
    """Imprime info básica de la respuesta."""
    print(f"{resp.request.method} {resp.url}")
    print(f"Status: {resp.status_code}")

    if expected_status is not None:
        ok = resp.status_code == expected_status
        print(f"Esperado: {expected_status} -> {'OK' if ok else 'ERROR'}")

    try:
        print("JSON:", resp.json())
    except Exception:
        print("Texto:", resp.text)

    print("-" * 60)


def test_get_blacklist():
    # GET /blacklist (sin filtros)
    resp = requests.get(f"{BASE_URL}/blacklist")
    show_response(resp, expected_status=200)

    # GET /blacklist con filtros de ejemplo
    resp = requests.get(f"{BASE_URL}/blacklist", params={"vehiculo_id": 1})
    show_response(resp, expected_status=200)


def test_post_blacklist():
    # POST /blacklist (ajusta el payload a tu esquema real)
    payload = {
        "vehiculo_id": 1,
        "parqueadero_id": 1,
        "motivo": "Prueba automática",
    }
    resp = requests.post(f"{BASE_URL}/blacklist", json=payload)
    show_response(resp, expected_status=201)


def test_patch_blacklist():
    # PATCH /blacklist/{id} (ajusta el id a uno existente)
    blacklist_id = 1
    payload = {
        "motivo": "Motivo actualizado por script",
    }
    resp = requests.patch(f"{BASE_URL}/blacklist/{blacklist_id}", json=payload)
    show_response(resp, expected_status=200)


if __name__ == "__main__":
    # Llama aquí las funciones que quieras probar
    test_get_blacklist()
    # test_post_blacklist()
    # test_patch_blacklist()
