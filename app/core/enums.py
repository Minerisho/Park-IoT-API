# app/core/enums.py
from enum import Enum

class GateType(str, Enum):
    ENTRADA_PARQUEADERO = "ENTRADA_PARQUEADERO"
    SALIDA_PARQUEADERO = "SALIDA_PARQUEADERO"
    ENTRADA_ZONA = "ENTRADA_ZONA"

class GateState(str, Enum):
    ABIERTA = "ABIERTA"
    CERRADA = "CERRADA"
    ABRIENDO = "ABRIENDO"
    CERRANDO = "CERRANDO"

class SensorType(str, Enum):
    ENTRADA_ZONA = "ENTRADA_ZONA"
    SALIDA_ZONA  = "SALIDA_ZONA"
    PRESENCIA_PALANCA = "PRESENCIA_PALANCA"

class DeviceType(str, Enum):
    ESP32  = "ESP32"
    CAMARA = "CAMARA"

class CommandType(str, Enum):
    OPEN_GATE  = "OPEN_GATE"
    CLOSE_GATE = "CLOSE_GATE"
    PING       = "PING"

class CommandStatus(str, Enum):
    PENDING = "PENDING"
    SENT    = "SENT"
    ACK     = "ACK"

class EventType(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA  = "SALIDA"

class IncidentType(str, Enum):
    SALIDA_SIN_ENTRADA   = "SALIDA_SIN_ENTRADA"
    PLACA_DESCONOCIDA    = "PLACA_DESCONOCIDA"
    ASIGNACION_FALLIDA   = "ASIGNACION_FALLIDA"
    MANUAL_OVERRIDE      = "MANUAL_OVERRIDE"
