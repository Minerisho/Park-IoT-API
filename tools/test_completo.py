import requests
import random
import string
import sys
import time

# Configuración
BASE_URL = "http://127.0.0.1:8000"

# Colores para la consola
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def log(msg, type="INFO"):
    if type == "INFO": print(f"{Colors.OKBLUE}[INFO]{Colors.ENDC} {msg}")
    elif type == "SUCCESS": print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} {msg}")
    elif type == "ERROR": print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {msg}")
    elif type == "WARN": print(f"{Colors.WARNING}[WARN]{Colors.ENDC} {msg}")

def check_status(response, expected_code=200, action=""):
    if response.status_code == expected_code:
        log(f"{action} - Status: {response.status_code}", "SUCCESS")
        return True
    else:
        log(f"{action} falló. Esperado: {expected_code}, Recibido: {response.status_code}", "ERROR")
        try:
            print(response.json())
        except:
            print(response.text)
        return False

# Generador de strings aleatorios
def random_str(length=5):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

def run_tests():
    session = requests.Session()
    
    print(f"{Colors.HEADER}=== INICIANDO TESTEO COMPLETO DE PARK-IOT API ==={Colors.ENDC}\n")

    # ---------------------------------------------------------
    # 1. GENERAL
    # ---------------------------------------------------------
    log("Testeando endpoints generales...")
    resp = session.get(f"{BASE_URL}/health")
    check_status(resp, 200, "Health Check")
    
    resp = session.get(f"{BASE_URL}/config")
    check_status(resp, 200, "Config Check")

    # ---------------------------------------------------------
    # 2. CREACIÓN (POST)
    # ---------------------------------------------------------
    print(f"\n{Colors.HEADER}--- FASE 1: CREACIÓN (POST) ---{Colors.ENDC}")
    
    # A. Crear Parqueadero
    p_data = {"nombre": f"Parqueadero Test {random_str()}", "direccion": "Calle Falsa 123"}
    resp = session.post(f"{BASE_URL}/parqueaderos", json=p_data)
    if not check_status(resp, 201, "Crear Parqueadero"): return
    parqueadero_id = resp.json()["id"]

    # B. Crear Vehículo
    placa_test = f"TST-{random.randint(100, 999)}" # Formato AAA-123
    v_data = {"placa": placa_test, "activo": True, "vehiculo_vip": False}
    resp = session.post(f"{BASE_URL}/vehiculos", json=v_data)
    if not check_status(resp, 201, "Crear Vehículo"): return
    vehiculo_id = resp.json()["id"]

    # C. Crear Zona
    z_data = {"parqueadero_id": parqueadero_id, "nombre": "Zona Norte", "capacidad": 10, "es_vip": False}
    resp = session.post(f"{BASE_URL}/zonas", json=z_data)
    if not check_status(resp, 201, "Crear Zona"): return
    zona_id = resp.json()["id"]

    # D. Crear Palancas
    # D1. Palanca Parqueadero (Entrada)
    pal_p_data = {"tipo": "ENTRADA_PARQUEADERO", "parqueadero_id": parqueadero_id, "abierto": False}
    resp = session.post(f"{BASE_URL}/palancas", json=pal_p_data)
    check_status(resp, 201, "Crear Palanca Parqueadero")
    palanca_p_id = resp.json()["id"]

    # D2. Palanca Zona (Entrada)
    pal_z_data = {"tipo": "ENTRADA_ZONA", "parqueadero_id": parqueadero_id, "zona_id": zona_id, "abierto": True}
    resp = session.post(f"{BASE_URL}/palancas", json=pal_z_data)
    check_status(resp, 201, "Crear Palanca Zona")
    palanca_z_id = resp.json()["id"]

    # E. Crear Sensores
    # E1. Sensor asociado a Palanca
    s_pal_data = {"tipo": "ENTRADA_PARQUEADERO", "nombre": "Sensor Entrada Principal", "palanca_id": palanca_p_id}
    resp = session.post(f"{BASE_URL}/sensores", json=s_pal_data)
    check_status(resp, 201, "Crear Sensor en Palanca")
    sensor_pal_id = resp.json()["id"]

    # E2. Sensor asociado a Zona
    s_zon_data = {"tipo": "ENTRADA_ZONA", "nombre": "Sensor Zona N", "zona_id": zona_id}
    resp = session.post(f"{BASE_URL}/sensores", json=s_zon_data)
    check_status(resp, 201, "Crear Sensor en Zona")
    sensor_zon_id = resp.json()["id"]

    # F. Crear Visita
    vis_data = {"vehiculo_id": vehiculo_id, "parqueadero_id": parqueadero_id}
    resp = session.post(f"{BASE_URL}/visitas", json=vis_data)
    check_status(resp, 201, "Crear Visita")
    visita_id = resp.json()["id"]

    # G. Crear Cámara
    cam_data = {"nombre": "Camara Acceso 1", "ubicacion": "ENTRADA", "device_index": 0}
    resp = session.post(f"{BASE_URL}/camaras", json=cam_data)
    check_status(resp, 201, "Crear Cámara")
    camara_id = resp.json()["id"]

    # ---------------------------------------------------------
    # 3. LECTURA (GET)
    # ---------------------------------------------------------
    print(f"\n{Colors.HEADER}--- FASE 2: LECTURA (GET) ---{Colors.ENDC}")
    
    check_status(session.get(f"{BASE_URL}/parqueaderos/{parqueadero_id}"), 200, "Get Parqueadero ID")
    check_status(session.get(f"{BASE_URL}/vehiculos/{vehiculo_id}"), 200, "Get Vehículo ID")
    check_status(session.get(f"{BASE_URL}/zonas/{zona_id}"), 200, "Get Zona ID")
    check_status(session.get(f"{BASE_URL}/palancas/{palanca_p_id}"), 200, "Get Palanca ID")
    check_status(session.get(f"{BASE_URL}/sensores/{sensor_pal_id}"), 200, "Get Sensor ID")
    check_status(session.get(f"{BASE_URL}/visitas/{visita_id}"), 200, "Get Visita ID")
    check_status(session.get(f"{BASE_URL}/camaras/{camara_id}"), 200, "Get Cámara ID")

    # Filtros
    check_status(session.get(f"{BASE_URL}/zonas?parqueadero_id={parqueadero_id}"), 200, "Listar Zonas con filtro")
    check_status(session.get(f"{BASE_URL}/vehiculos?activo=true"), 200, "Listar Vehículos activos")
    
    # Topología
    log("Probando Topología...")
    resp = session.get(f"{BASE_URL}/parqueaderos/topologia")
    if check_status(resp, 200, "Get Topología"):
        data = resp.json()
        if any(p['id_parqueadero'] == parqueadero_id for p in data.values()):
            log("Topología contiene el parqueadero creado", "SUCCESS")
        else:
            log("El parqueadero no apareció en topología", "WARN")

    # ---------------------------------------------------------
    # 4. ACTUALIZACIÓN (PATCH)
    # ---------------------------------------------------------
    print(f"\n{Colors.HEADER}--- FASE 3: ACTUALIZACIÓN (PATCH) ---{Colors.ENDC}")

    # Actualizar Parqueadero
    check_status(session.patch(f"{BASE_URL}/parqueaderos/{parqueadero_id}", json={"nombre": "Nombre Nuevo"}), 200, "Patch Parqueadero")
    
    # Actualizar Zona (capacidad)
    check_status(session.patch(f"{BASE_URL}/zonas/{zona_id}", json={"capacidad": 50, "conteo_actual": 5}), 200, "Patch Zona")
    
    # Actualizar Palanca (abrir)
    check_status(session.patch(f"{BASE_URL}/palancas/{palanca_p_id}", json={"abierto": True}), 200, "Patch Palanca")
    
    # Actualizar Sensor
    check_status(session.patch(f"{BASE_URL}/sensores/{sensor_pal_id}", json={"activo": False}), 200, "Patch Sensor")
    
    # Actualizar Visita (salida)
    # Nota: ts_salida debe ser string ISO, o datetime
    from datetime import datetime
    check_status(session.patch(f"{BASE_URL}/visitas/{visita_id}", json={"ts_salida": str(datetime.now())}), 200, "Patch Visita (Salida)")

    # ---------------------------------------------------------
    # 5. CÁMARA Y VISIÓN
    # ---------------------------------------------------------
    print(f"\n{Colors.HEADER}--- FASE 4: PRUEBA DE VISIÓN ---{Colors.ENDC}")
    log("Intentando captura (Esto puede fallar si no hay webcam real conectada, es normal)")
    try:
        # Timeout corto para no congelar el test si no hay camara
        resp = session.get(f"{BASE_URL}/camaras/{camara_id}/capturar", timeout=5)
        if resp.status_code == 200:
            log("Captura exitosa (o simulada)", "SUCCESS")
        else:
            log(f"Endpoint captura respondió: {resp.status_code} (Esperable sin hardware)", "WARN")
    except requests.exceptions.RequestException as e:
        log(f"Error conectando con cámara (Esperable sin hardware): {e}", "WARN")

    # ---------------------------------------------------------
    # 6. BORRADO (DELETE)
    # ---------------------------------------------------------
    print(f"\n{Colors.HEADER}--- FASE 5: BORRADO (DELETE) ---{Colors.ENDC}")
    # El orden importa por las Foreign Keys

    # 1. Borrar Visita
    check_status(session.delete(f"{BASE_URL}/visitas/{visita_id}"), 204, "Delete Visita")
    
    # 2. Borrar Sensores
    check_status(session.delete(f"{BASE_URL}/sensores/{sensor_pal_id}"), 200, "Delete Sensor Palanca")
    check_status(session.delete(f"{BASE_URL}/sensores/{sensor_zon_id}"), 200, "Delete Sensor Zona")

    # 3. Borrar Palancas 
    # Nota: Verificamos si existe el endpoint DELETE en palancas (en tu archivo router no aparecía, pero en test_delete.py sí)
    resp = session.delete(f"{BASE_URL}/palancas/{palanca_p_id}")
    if resp.status_code == 405:
        log("Delete Palanca no implementado (Método no permitido)", "WARN")
    else:
        check_status(resp, 200, "Delete Palanca (Parqueadero)")
        session.delete(f"{BASE_URL}/palancas/{palanca_z_id}") # Limpieza silenciosa de la otra

    # 4. Borrar Zona
    check_status(session.delete(f"{BASE_URL}/zonas/{zona_id}"), 200, "Delete Zona")

    # 5. Borrar Vehículo
    check_status(session.delete(f"{BASE_URL}/vehiculos/{vehiculo_id}"), 200, "Delete Vehículo")
    
    # 6. Borrar Cámara
    check_status(session.delete(f"{BASE_URL}/camaras/{camara_id}"), 204, "Delete Cámara")

    # 7. Borrar Parqueadero
    check_status(session.delete(f"{BASE_URL}/parqueaderos/{parqueadero_id}"), 200, "Delete Parqueadero")

    print(f"\n{Colors.HEADER}=== TEST FINALIZADO ==={Colors.ENDC}")

if __name__ == "__main__":
    try:
        run_tests()
    except requests.exceptions.ConnectionError:
        print(f"{Colors.FAIL}[CRITICAL] No se pudo conectar a {BASE_URL}. ¿Está corriendo el servidor?{Colors.ENDC}")