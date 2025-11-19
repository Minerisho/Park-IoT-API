import cv2
import numpy as np
from ultralytics import YOLO
import easyocr
import re
import os
from datetime import datetime

class LectorPlacas:
    def __init__(
        self,
        min_confidence_ocr: float = 0.4,
        use_gpu: bool = False,
        guardar_img: bool = True,
        nivel_procesamiento: float = 0.5, 
        dir_capturas: str = "app/vision/capturas/capturas_completas", 
        dir_procesadas: str = "app/vision/capturas/placas_procesadas",
        model_path: str = "app/vision/modelo/license_plate_detector.pt"
    ) -> None:
        self.min_confidence_ocr = min_confidence_ocr
        self.guardar_img = guardar_img
        # Aseguramos que esté entre 0 y 1
        self.nivel_procesamiento = max(0.0, min(1.0, nivel_procesamiento))
        self.dir_capturas = dir_capturas
        self.dir_procesadas = dir_procesadas
        
        if self.guardar_img:
            os.makedirs(self.dir_capturas, exist_ok=True)
            os.makedirs(self.dir_procesadas, exist_ok=True)
        
        print("Cargando modelo OCR...")
        self.reader = easyocr.Reader(['en'], gpu=use_gpu)
        
        print(f"Cargando modelo YOLO: {model_path}...")
        self.model = YOLO(model_path) 

        # Diccionarios de corrección
        self.dict_char_to_int = {'O': '0', 'I': '1', 'J': '3', 'A': '4', 'G': '6', 'S': '5'}
        self.dict_int_to_char = {'0': 'O', '1': 'I', '3': 'J', '4': 'A', '6': 'G', '5': 'S'}

    def _generar_nombre_archivo(self):
        timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
        return f"img_{timestamp}.png"

    def _procesar_imagen_placa(self, img_placa):
        """
        Mezcla la imagen original con la procesada según self.nivel_procesamiento.
        """
        # 1. Versión Suave (Base): Solo escala de grises
        gray_base = cv2.cvtColor(img_placa, cv2.COLOR_BGR2GRAY)
        
        # Si el nivel es 0, no hacemos nada más (ahorramos proceso)
        if self.nivel_procesamiento <= 0.05:
            return gray_base

        # 2. Versión Agresiva: Filtro Amarillo + Binarización Otsu
        img_proc = img_placa.copy()
        
        # Amarillo -> Blanco
        hsv = cv2.cvtColor(img_proc, cv2.COLOR_BGR2HSV)
        lower_yellow = np.array([15, 80, 80]) 
        upper_yellow = np.array([35, 255, 255])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        img_proc[mask > 0] = [255, 255, 255]
        
        # Binarización fuerte
        gray_proc = cv2.cvtColor(img_proc, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray_proc, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Si el nivel es 1.0 (o muy cercano), devolvemos la binaria pura
        if self.nivel_procesamiento >= 0.95:
            return binary
            
        # 3. Mezcla (Blending)
        # Fórmula: Final = (Agresiva * alpha) + (Suave * beta)
        # Esto restaura detalles perdidos por el binarizado fuerte
        alpha = self.nivel_procesamiento
        beta = 1.0 - alpha
        
        # addWeighted funde ambas imágenes
        img_final = cv2.addWeighted(binary, alpha, gray_base, beta, 0)
        
        return img_final

    def _formatear_texto(self, texto_raw):
        limpio = re.sub(r'[^A-Za-z0-9]', '', texto_raw).upper()
        if len(limpio) == 6:
            letras_final = [self.dict_int_to_char.get(c, c) for c in limpio[:3]]
            nums_final = [self.dict_char_to_int.get(c, c) for c in limpio[3:]]
            return f"{''.join(letras_final)} - {''.join(nums_final)}"
        if len(limpio) > 3:
            return f"{limpio[:3]} - {limpio[3:]}"
        return limpio

    def _crear_imagen_compuesta(self, frame, recorte_placa, encontro_placa=True):
        h_frame = frame.shape[0]
        
        if not encontro_placa:
            h_recorte, w_recorte = 150, 400
            recorte_placa = np.zeros((h_recorte, w_recorte, 3), dtype=np.uint8)
            cv2.putText(recorte_placa, "NO PLACA", (10, 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        
        h_recorte, w_recorte = recorte_placa.shape[:2]
        canvas_ancho = 400 
        canvas_recorte = np.zeros((h_frame, canvas_ancho, 3), dtype=np.uint8)
        
        if w_recorte > canvas_ancho:
            scale = canvas_ancho / w_recorte
            w_recorte = canvas_ancho
            h_recorte = int(h_recorte * scale)
            recorte_placa = cv2.resize(recorte_placa, (w_recorte, h_recorte))
        
        y_offset = max(0, (h_frame - h_recorte) // 2)
        h_paste = min(h_recorte, h_frame - y_offset)
        
        if h_paste > 0 and w_recorte > 0:
            canvas_recorte[y_offset:y_offset+h_paste, :w_recorte] = recorte_placa[:h_paste, :]
        
        return cv2.hconcat([frame, canvas_recorte])

    def capturar_placa(self, camera_index: int):
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print(f"Error cámara {camera_index}")
            return "ERR_CAM", 0.0, None, None
        
        for _ in range(5): cap.read()
        ret, frame = cap.read()
        cap.release()
        
        if not ret: return "ERR_FRAME", 0.0, None, None

        # Predicción
        results = self.model.predict(frame, verbose=False, conf=0.4)
        
        placa_recortada = None
        conf_deteccion = 0.0
        
        if len(results[0].boxes) > 0:
            best_box = results[0].boxes[0]
            coords = best_box.xyxy[0].cpu().numpy().astype(int)
            conf_deteccion = float(best_box.conf[0])
            x1, y1, x2, y2 = coords
            y1, x1 = max(0, y1), max(0, x1)
            y2, x2 = min(frame.shape[0], y2), min(frame.shape[1], x2)
            placa_recortada = frame[y1:y2, x1:x2]

        ruta_final_completa = None
        ruta_final_procesada = None
        
        if self.guardar_img:
            nombre_archivo = self._generar_nombre_archivo()
            img_compuesta = self._crear_imagen_compuesta(
                frame, 
                placa_recortada if placa_recortada is not None else np.array([]), 
                encontro_placa=(placa_recortada is not None)
            )
            ruta_final_completa = os.path.join(self.dir_capturas, nombre_archivo)
            cv2.imwrite(ruta_final_completa, img_compuesta)

        if placa_recortada is None:
            return "NO DETECTADO", 0.0, ruta_final_completa, None

        # --- AQUI USAMOS EL NIVEL DE PROCESAMIENTO ---
        placa_para_ocr = self._procesar_imagen_placa(placa_recortada)

        if self.guardar_img:
            ruta_final_procesada = os.path.join(self.dir_procesadas, nombre_archivo)
            cv2.imwrite(ruta_final_procesada, placa_para_ocr)

        # OCR
        ocr_results = self.reader.readtext(placa_para_ocr)
        texto_final = "NO LEIDO"
        confianza_ocr = 0.0
        
        validos = [res for res in ocr_results if res[2] >= self.min_confidence_ocr]
        
        if validos:
            texto_concat = "".join([res[1] for res in validos])
            confianza_promedio = sum([res[2] for res in validos]) / len(validos)
            texto_final = self._formatear_texto(texto_concat)
            confianza_ocr = confianza_promedio
        
        return texto_final, confianza_ocr, ruta_final_completa, ruta_final_procesada
