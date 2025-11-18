# usar_camara.py
from plate_recognizer import ColombianPlateRecognizer


def main() -> None:
    recognizer = ColombianPlateRecognizer(
        output_dir="plates_output",
        min_confidence_ocr=0.4,
        use_gpu=False,  # pon True si tienes GPU con CUDA y EasyOCR configurado
    )

    camera_index = 0  # Cambia este valor si usas otra cámara
    plate, confidence, image_path = recognizer.capture_and_read_plate(camera_index)

    if plate is None:
        print("No se detectó una placa colombiana válida (ABC-123).")
    else:
        print(f"Placa: {plate}")
        print(f"Confianza: {confidence:.2f}%")
        print(f"Imagen procesada guardada en: {image_path}")


if __name__ == "__main__":
    main()
