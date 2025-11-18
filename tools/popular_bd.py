import requests
import random
import string
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
BASE_URL = "http://127.0.0.1:8000"

def log(msg):
    print(f"[+] {msg}")

def error_log(msg, resp):
    print(f"[!] ERROR: {msg} (Status: {resp.status_code})")
    print(f"    Detalle: {resp.text}")

def generate_plate():
    """Genera una placa formato AAA-123"""
    letters = "".join(random.choices(string.ascii_uppercase, k=3))
    numbers = "".join(random.choices(string.digits, k=3))
    return f"{letters}-{numbers}"

def main():
    session = requests.Session()

    # ---------------------------------------------------------
    # 1. CREAR PARQUEADERO
    # ---------------------------------------------------------
    print("--- 1. CREANDO PARQUEADERO ---")
    p_data = {
        "nombre": "Parqueadero Central",
        "direccion": "Carrera 27 #10-20"
    }
    resp = session.post(f"{BASE_URL}/parqueaderos", json=p_data)
    if resp.status_code != 201:
        error_log("Falló crear parqueadero", resp)
        return
    parqueadero_id = resp.json()["id"]
    log(f"Parqueadero creado: ID {parqueadero_id}")

    # ---------------------------------------------------------
    # 2. CREAR PALANCAS PRINCIPALES (ENTRADA Y SALIDA)
    # ---------------------------------------------------------
    print("\n--- 2. CREANDO PALANCAS PRINCIPALES ---")
    # Palanca Entrada Principal
    pal_in_data = {
        "tipo": "ENTRADA_PARQUEADERO",
        "parqueadero_id": parqueadero_id,
        "abierto": False
    }
    resp = session.post(f"{BASE_URL}/palancas", json=pal_in_data)
    log(f"Palanca Entrada Principal creada (ID: {resp.json()['id']})")

    # Palanca Salida Principal
    pal_out_data = {
        "tipo": "SALIDA_PARQUEADERO",
        "parqueadero_id": parqueadero_id,
        "abierto": False
    }
    resp = session.post(f"{BASE_URL}/palancas", json=pal_out_data)
    log(f"Palanca Salida Principal creada (ID: {resp.json()['id']})")

    # ---------------------------------------------------------
    # 3. CREAR 3 ZONAS (1 VIP) CON SUS ELEMENTOS
    # ---------------------------------------------------------
    print("\n--- 3. CREANDO ZONAS, PALANCAS Y SENSORES ---")
    zona_ids = []
    
    for i in range(3):
        is_vip = (i == 0)  # La primera es VIP
        nombre_zona = f"Zona {'VIP' if is_vip else 'General'} {i+1}"
        
        # A. Crear Zona
        z_data = {
            "parqueadero_id": parqueadero_id,
            "nombre": nombre_zona,
            "es_vip": is_vip,
            "capacidad": 5
        }
        resp = session.post(f"{BASE_URL}/zonas", json=z_data)
        zona_obj = resp.json()
        z_id = zona_obj["id"]
        zona_ids.append(z_id)
        log(f"Zona creada: {nombre_zona} (ID: {z_id}, VIP: {is_vip})")

        # B. Crear 1 Palanca de Entrada para la zona
        pal_z_data = {
            "tipo": "ENTRADA_ZONA",
            "parqueadero_id": parqueadero_id,
            "zona_id": z_id,
            "abierto": False
        }
        resp = session.post(f"{BASE_URL}/palancas", json=pal_z_data)
        pal_z_id = resp.json()["id"]
        log(f"  -> Palanca Entrada Zona creada (ID: {pal_z_id})")

        # C. Crear 2 Sensores (Entrada y Salida)
        # C1. Sensor Entrada (Asociado a la palanca y la zona)
        s_in_data = {
            "tipo": "ENTRADA_ZONA",
            "nombre": f"Sensor Entrada {nombre_zona}",
            "zona_id": z_id,
            "palanca_id": pal_z_id,
            "activo": True
        }
        session.post(f"{BASE_URL}/sensores", json=s_in_data)
        
        # C2. Sensor Salida (Solo asociado a la zona, ya que no pediste palanca de salida de zona)
        s_out_data = {
            "tipo": "SALIDA_ZONA",
            "nombre": f"Sensor Salida {nombre_zona}",
            "zona_id": z_id,
            "activo": True
        }
        session.post(f"{BASE_URL}/sensores", json=s_out_data)
        log(f"  -> Sensores de entrada y salida creados para {nombre_zona}")

    # ---------------------------------------------------------
    # 4. CREAR 20 VEHÍCULOS (5 VIP, 5 LISTA NEGRA, 10 NORMALES)
    # ---------------------------------------------------------
    print("\n--- 4. CREANDO 20 VEHÍCULOS ---")
    vehiculos_creados = []

    for i in range(20):
        es_vip = False
        en_lista_negra = False

        if i < 5:
            es_vip = True          # Primeros 5 VIP
        elif i < 10:
            en_lista_negra = True  # Siguientes 5 Lista Negra
        
        v_data = {
            "placa": generate_plate(),
            "activo": True,
            "vehiculo_vip": es_vip,
            "en_lista_negra": en_lista_negra
        }
        
        resp = session.post(f"{BASE_URL}/vehiculos", json=v_data)
        if resp.status_code == 201:
            v_obj = resp.json()
            vehiculos_creados.append(v_obj)
            tipo = "VIP" if es_vip else ("BLACKLIST" if en_lista_negra else "NORMAL")
            # Imprimir solo algunos para no saturar consola
            if i == 0 or i == 5 or i == 10 or i == 19: 
                log(f"Vehículo creado ({i+1}/20): {v_obj['placa']} [{tipo}]")
        else:
            error_log("Error creando vehículo", resp)

    # ---------------------------------------------------------
    # 5. AÑADIR DOS CÁMARAS
    # ---------------------------------------------------------
    print("\n--- 5. CREANDO CÁMARAS ---")
    # Cámara 1: Entrada
    c1_data = {
        "nombre": "Cámara Principal Entrada",
        "device_index": 1,
        "ubicacion": "entrada",
        "activo": True
    }
    session.post(f"{BASE_URL}/camaras", json=c1_data)
    log("Cámara de Entrada creada (Index 1)")

    # Cámara 2: Salida
    c2_data = {
        "nombre": "Cámara Principal Salida",
        "device_index": 2,
        "ubicacion": "salida",
        "activo": True
    }
    session.post(f"{BASE_URL}/camaras", json=c2_data)
    log("Cámara de Salida creada (Index 2)")

    # ---------------------------------------------------------
    # 6. AÑADIR 5 VISITAS
    # ---------------------------------------------------------
    print("\n--- 6. CREANDO VISITAS ---")
    # Tomamos 5 vehículos al azar de los creados
    vehiculos_muestra = random.sample(vehiculos_creados, 5)

    for i, veh in enumerate(vehiculos_muestra):
        # Creamos tiempos diferentes restando minutos al momento actual
        tiempo_entrada = datetime.now() - timedelta(hours=1, minutes=i*10)
        
        vis_data = {
            "vehiculo_id": veh["id"],
            "parqueadero_id": parqueadero_id,
            "ts_entrada": tiempo_entrada.isoformat()
        }
        
        resp = session.post(f"{BASE_URL}/visitas", json=vis_data)
        if resp.status_code == 201:
            log(f"Visita creada para placa {veh['placa']} a las {tiempo_entrada.strftime('%H:%M')}")
        else:
            error_log("Error creando visita", resp)

    print("\n=== PROCESO TERMINADO EXITOSAMENTE ===")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("[!] No se pudo conectar al servidor. Asegúrate de que la API esté corriendo en 127.0.0.1:8000")