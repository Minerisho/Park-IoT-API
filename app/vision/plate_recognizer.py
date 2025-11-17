# plate_recognizer.py
import os
import time
from typing import Optional, Tuple

import cv2
import numpy as np
import easyocr


def normalize_colombian_plate(text: str) -> Optional[str]:
    """
    Normaliza un texto crudo detectado por OCR al formato de placa colombiana
    de carro particular: 'ABC-123'.

    - Elimina espacios y caracteres no alfanuméricos.
    - Verifica que tenga exactamente 3 letras seguidas de 3 dígitos.
    - Devuelve la placa normalizada 'ABC-123' o None si no cumple el formato.
    """
    if text is None:
        return None

    cleaned_chars = []
    for ch in text.upper():
        if ch.isalnum():
            cleaned_chars.append(ch)

    cleaned = "".join(cleaned_chars)

    if len(cleaned) != 6:
        return None

    letters = cleaned[:3]
    digits = cleaned[3:]

    if not letters.isalpha():
        return None

    if not digits.isdigit():
        return None

    normalized = letters + "-" + digits
    return normalized


class ColombianPlateRecognizer:
    """
    Clase para capturar una imagen desde una cámara web, detectar una placa
    colombiana de carro particular, recortarla, procesarla y extraer el texto
    usando OCR (EasyOCR – modelo preentrenado).

    Dependencias:
        pip install opencv-python easyocr numpy

    Uso típico:
        recognizer = ColombianPlateRecognizer(output_dir="plates_output")
        plate, confidence, image_path = recognizer.capture_and_read_plate(0)
    """

    def __init__(
        self,
        output_dir: str = "plates_output",
        min_confidence_ocr: float = 0.4,
        use_gpu: bool = False,
    ) -> None:
        """
        Parámetros:
            output_dir: Carpeta donde se guardarán las imágenes recortadas/procesadas.
            min_confidence_ocr: confianza mínima (0–1) para aceptar una lectura de OCR.
            use_gpu: True si quieres usar GPU con EasyOCR (si tienes CUDA).
        """
        self.output_dir = output_dir
        self.min_confidence_ocr = min_confidence_ocr

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

        # EasyOCR: modelo preentrenado de reconocimiento de texto.
        # 'en' basta para letras y números de la placa.
        self.reader = easyocr.Reader(
            ["en"],
            gpu=use_gpu,
        )

    def capture_and_read_plate(
        self,
        camera_index: int,
    ) -> Tuple[Optional[str], float, Optional[str]]:
        """
        Captura una imagen de la cámara indicada, detecta y recorta la placa,
        procesa la imagen recortada y extrae el texto de la placa.

        Parámetros:
            camera_index: índice de la cámara (0, 1, 2, ...).

        Devuelve:
            (plate_text, confidence_percent, processed_image_path)

            - plate_text: str con la placa en formato 'ABC-123' si es válida,
              o None si NO se detectó una placa colombiana de carro particular.
            - confidence_percent: confianza del OCR en porcentaje (0.0 a 100.0).
            - processed_image_path: ruta de la imagen recortada y procesada
              si la placa es válida, o None si no se detectó placa válida.
        """
        frame = self._capture_frame(camera_index)

        if frame is None:
            return None, 0.0, None

        roi = self._find_plate_roi(frame)
        
        if roi is None:
            return None, 0.0, None

        processed = self._preprocess_plate_image(roi)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"plate_{timestamp}.png"
        output_path = os.path.join(self.output_dir, filename)

        # Guardamos SOLO la imagen procesada
        success = cv2.imwrite(output_path, processed)

        if not success:
            return None, 0.0, None

        plate_text, confidence = self._recognize_plate_from_image(processed)

        if plate_text is None:
            # No es placa colombiana válida: borramos la imagen procesada
            try:
                os.remove(output_path)
            except OSError:
                pass
            return None, 0.0, None

        confidence_percent = confidence * 100.0
        return plate_text, confidence_percent, output_path

    def _capture_frame(self, camera_index: int) -> Optional[np.ndarray]:
        """
        Captura un solo frame de la cámara indicada.
        """
        # En Windows, CAP_DSHOW reduce algunos problemas con webcams.
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

        if not cap.isOpened():
            return None

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None

        return frame

    def _find_plate_roi(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Detecta una región de interés (ROI) que probablemente sea una placa
        colombiana basándose en el color amarillo y la forma rectangular.

        - Convierte la imagen a HSV.
        - Segmenta el color amarillo.
        - Aplica operaciones morfológicas.
        - Busca contornos con relación de aspecto similar a una placa.
        - Recorta la región candidata, recortando un poco la parte inferior
          para evitar el texto del municipio.

        Devuelve:
            ROI de la placa como np.ndarray en BGR o None si no se encuentra.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Rangos aproximados de amarillo en HSV (pueden ajustarse según la cámara)
        lower_yellow = np.array([15, 40, 40], dtype=np.uint8)
        upper_yellow = np.array([40, 255, 255], dtype=np.uint8)

        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours is None or len(contours) == 0:
            return None

        frame_height, frame_width = frame.shape[:2]
        frame_area = float(frame_width * frame_height)

        best_rect = None
        best_area = 0.0

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = float(w * h)

            # Filtrar contornos muy pequeños
            if area < 0.0005 * frame_area:
                continue

            aspect_ratio = float(w) / float(h)

            # Placas típicamente más anchas que altas (ajustable)
            if aspect_ratio < 2.5 or aspect_ratio > 6.0:
                continue

            if area > best_area:
                best_area = area
                best_rect = (x, y, w, h)

        if best_rect is None:
            return None

        x, y, w, h = best_rect

        # Recortamos la parte inferior (ej. 20%) para evitar texto del municipio.
        top = y
        bottom = y + h
        bottom_reduced = y + int(h * 0.8)

        if bottom_reduced <= top:
            bottom_reduced = bottom

        roi = frame[top:bottom_reduced, x : x + w].copy()
        if roi.size == 0:
            return None

        return roi

    def _preprocess_plate_image(self, roi: np.ndarray) -> np.ndarray:
        """
        Preprocesa la imagen recortada de la placa para facilitar el OCR.

        - Escala la imagen (zoom).
        - Segmenta el amarillo para "blanquear" todo lo que no sea placa.
        - Convierte a escala de grises.
        - Aplica desenfoque suave y mejora de contraste.
        - Aplica umbral (Otsu) para binarizar.
        - Invierte la imagen si la media es muy clara (para tener texto oscuro).
        """
        # Escalamos para mejorar la lectura del OCR
        roi_resized = cv2.resize(
            roi,
            None,
            fx=2.0,
            fy=2.0,
            interpolation=cv2.INTER_CUBIC,
        )

        # Segmentar amarillo dentro del ROI para resaltar solo la placa
        hsv = cv2.cvtColor(roi_resized, cv2.COLOR_BGR2HSV)
        lower_yellow = np.array([15, 40, 40], dtype=np.uint8)
        upper_yellow = np.array([40, 255, 255], dtype=np.uint8)
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # Mantenemos solo la zona amarilla y ponemos el resto en blanco
        plate_only = cv2.bitwise_and(roi_resized, roi_resized, mask=mask_yellow)
        white_background = np.full_like(roi_resized, 255, dtype=np.uint8)
        mask_yellow_3ch = cv2.merge([mask_yellow, mask_yellow, mask_yellow])
        plate_on_white = np.where(mask_yellow_3ch == 0, white_background, plate_only)

        gray = cv2.cvtColor(plate_on_white, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_clahe = clahe.apply(gray)

        _, binary = cv2.threshold(
            gray_clahe,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )

        mean_val = float(np.mean(binary))
        if mean_val > 127.0:
            binary = cv2.bitwise_not(binary)

        return binary

    def _recognize_plate_from_image(
        self,
        image: np.ndarray,
    ) -> Tuple[Optional[str], float]:
        """
        Ejecuta OCR sobre una imagen de placa procesada y devuelve la mejor
        placa colombiana encontrada.

        Devuelve:
            (plate_text, confidence)

            - plate_text: 'ABC-123' si se detecta una placa colombiana válida,
              o None si no se encuentra.
            - confidence: valor entre 0.0 y 1.0 (EasyOCR).
        """
        # EasyOCR espera una imagen en BGR o RGB. Convertimos a BGR si es binaria.
        if len(image.shape) == 2:
            ocr_input = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            ocr_input = image

        results = self.reader.readtext(ocr_input)

        if results is None or len(results) == 0:
            return None, 0.0

        best_plate = None
        best_conf = 0.0

        for bbox, text, conf in results:
            if text is None:
                continue

            normalized = normalize_colombian_plate(text)
            if normalized is None:
                continue

            if conf < self.min_confidence_ocr:
                continue

            if conf > best_conf:
                best_conf = conf
                best_plate = normalized

        if best_plate is None:
            return None, 0.0

        return best_plate, best_conf
