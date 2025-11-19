# usar_camara.py
from lector_placas import LectorPlacas


def main() -> None:
    lector = LectorPlacas(
        guardar_img=True, 
        nivel_procesamiento=0.2 
    )
    
    placa, conf, ruta_full, ruta_rec = lector.capturar_placa(0)
    
    print(f"\n>>> PLACA: {placa}")
    print(f">>> CONFIANZA: {conf:.2f}")
    print(f">>> Imagen guardada en: {ruta_full}")


if __name__ == "__main__":
    main()
