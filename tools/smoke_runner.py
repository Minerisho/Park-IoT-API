import requests
import string
import random

BASE = "http://127.0.0.1:8000"

def rstr(n=6):
    return "".join(random.choices(string.hexdigits.lower(), k=n))

def call(method, path, **kwargs):
    url = f"{BASE}{path}"
    resp = requests.request(method, url, **kwargs)
    ok = 200 <= resp.status_code < 300
    print(f"{method.upper():4} {path} -> {resp.status_code}")
    if not ok:
        try:
            print("Body:", resp.text)
        except Exception:
            pass
        resp.raise_for_status()
    return resp

def main():
    tag = rstr()

    # 1) Health
    call("GET", "/health")

    # 2) Crear parqueadero
    rp = call("POST", "/parqueaderos", json={
        "nombre": f"Parqueadero Central {tag}",
        "direccion": "Cra 1 # 2-34"
    })
    parqueadero = rp.json()
    print("Parqueadero:", parqueadero)
    p_id = parqueadero["id"]

    # 3) Zonas (VIP y B)
    rvip = call("POST", "/zonas", json={
        "parqueadero_id": p_id,
        "nombre": "VIP",
        "es_vip": True,
        "capacidad": 5,
        "orden": 0
    })
    zona_vip = rvip.json()
    print("Zona VIP:", zona_vip)

    rzb = call("POST", "/zonas", json={
        "parqueadero_id": p_id,
        "nombre": "B",
        "es_vip": False,
        "capacidad": 2,
        "orden": 2
    })
    zona_b = rzb.json()
    print("Zona B:", zona_b)
    z_b_id = zona_b["id"]

    # 4) Palancas (entrada/salida parqueadero + entrada ZB)
    rpg_in = call("POST", "/palancas", json={"parqueadero_id": p_id, "tipo": "ENTRADA_PARQUEADERO"})
    rpg_out = call("POST", "/palancas", json={"parqueadero_id": p_id, "tipo": "SALIDA_PARQUEADERO"})
    rzg_in = call("POST", "/palancas", json={"zona_id": z_b_id, "tipo": "ENTRADA_ZONA"})
    print("Palanca entrada parqueadero:", rpg_in.json())
    print("Palanca salida parqueadero:", rpg_out.json())
    print("Palanca entrada zona B:", rzg_in.json())

    # 5) Sensores de la zona B (IN / OUT)
    rin = call("POST", "/sensores", json={
        "tipo": "ENTRADA_ZONA",
        "nombre": f"IR IN B {tag}",
        "zona_id": z_b_id
    })
    sin = rin.json()
    print("Sensor IN:", sin)

    rout = call("POST", "/sensores", json={
        "tipo": "SALIDA_ZONA",
        "nombre": f"IR OUT B {tag}",
        "zona_id": z_b_id
    })
    sout = rout.json()
    print("Sensor OUT:", sout)

    sin_id = sin["id"]
    sout_id = sout["id"]

    # 6) Triggers para dejar B en 2/2 y luego 1/2
    def trig(sid, ev):
        return call("POST", f"/sensores/{sid}/trigger", json={"evento": ev})

    trig(sin_id, "ENTRADA")  # B: 1/2
    trig(sin_id, "ENTRADA")  # B: 2/2 (llena)
    trig(sout_id, "SALIDA")  # B: 1/2 (dejamos un hueco)

    # 7) Accionar palanca de entrada del parqueadero (solo para registrar eventos)
    pid_in = rpg_in.json()["id"]
    # abrir / cerrar por "accion"
    call("POST", f"/palancas/{pid_in}/accion", json={"accion": "ABRIR"})
    # fijar explícitamente el estado (usa tu schema)
    call("POST", f"/palancas/{pid_in}/estado", json={"estado": "ABIERTA", "nota": "test abrir"})  # body requerido

    call("POST", f"/palancas/{pid_in}/accion", json={"accion": "CERRAR"})
    call("POST", f"/palancas/{pid_in}/estado", json={"estado": "CERRADA", "nota": "test cerrar"})  # body requerido


    # 8) Visita NO-VIP que debe ENTRAR (hay 1/2 en B)
    placa_demo = f"ABC{random.randint(100,999)}"
    r_ent1 = call("POST", "/visitas/entrada", json={"placa": placa_demo, "parqueadero_id": p_id})
    print("Visita entrada OK:", r_ent1.json())
    # Ahora B vuelve a estar en 2/2

    # 9) Segundo intento de visita NO-VIP cuando B está llena -> 409 con action=DERIVAR_SALIDA
    try:
        call("POST", "/visitas/entrada", json={"placa": f"XYZ{random.randint(100,999)}", "parqueadero_id": p_id})
        print("Visita extra inesperadamente OK (debería derivar a salida)")
    except requests.HTTPError as e:
        if e.response.status_code == 409:
            data = e.response.json()
            # Aceptamos tanto string como dict de detail
            if isinstance(data, dict) and isinstance(data.get("detail"), dict):
                detail = data["detail"]
                print("Visita extra correctamente rechazada:", detail)
                assert detail.get("action") == "DERIVAR_SALIDA", "Se esperaba action=DERIVAR_SALIDA"
            else:
                print("Visita extra correctamente rechazada:", data)
        else:
            raise

    # 10) Resumen
    print("== Resumen ==")
    print("GET  /parqueaderos ->", call("GET", "/parqueaderos").status_code)
    print("GET  /zonas ->", call("GET", "/zonas").status_code)
    print("GET  /palancas (por parqueadero) ->", call("GET", f"/palancas?parqueadero_id={p_id}").status_code)
    print("GET  /sensores ->", call("GET", "/sensores").status_code)

    # Eventos zona B
    rev_all = call("GET", f"/eventos-zona?zona_id={z_b_id}&limit=10")
    print("Eventos ZB (todos):", rev_all.json())

    # Eventos palanca entrada
    rep = call("GET", f"/eventos-parqueadero?palanca_id={pid_in}&limit=5")
    print("Eventos palanca entrada (recientes):", rep.json())
    assert len(rep.json()) >= 2, "Faltan eventos de palanca"
    
    if rep.json():
        peid = rep.json()[0]["id"]
        red = call("GET", f"/eventos-parqueadero/{peid}")
        print("Detalle evento palanca:", red.json())




    print("Smoke OK ✅")

if __name__ == "__main__":
    main()
