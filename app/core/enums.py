from enum import Enum

class Type(str, Enum):
    """Tipo genérico para palancas y sensores."""

    ENTRADA_PARQUEADERO = "ENTRADA_PARQUEADERO"
    SALIDA_PARQUEADERO = "SALIDA_PARQUEADERO"
    ENTRADA_ZONA = "ENTRADA_ZONA"
    SALIDA_ZONA = "SALIDA_ZONA"
