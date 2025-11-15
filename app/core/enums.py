from enum import Enum

class GateType(str, Enum):
    ENTRADA_PARQUEADERO = "ENTRADA_PARQUEADERO"
    SALIDA_PARQUEADERO  = "SALIDA_PARQUEADERO"
    ENTRADA_ZONA        = "ENTRADA_ZONA"
    SALIDA_ZONA         = "SALIDA_ZONA"

class GateState(str, Enum):
    ABIERTA = "ABIERTA"
    CERRADA = "CERRADA"

class SensorType(str, Enum):
    # ➜ habilitamos sensores tanto para parqueadero como para zona
    ENTRADA_PARQUEADERO = "ENTRADA_PARQUEADERO"
    SALIDA_PARQUEADERO  = "SALIDA_PARQUEADERO"
    ENTRADA_ZONA        = "ENTRADA_ZONA"
    SALIDA_ZONA         = "SALIDA_ZONA"
