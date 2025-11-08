# anpr_co.py
# -*- coding: utf-8 -*-

import os
import re
import cv2
import csv
import time
import queue
import argparse
import threading
from datetime import datetime
from typing import List, Tuple, Optional

import numpy as np
from ultralytics import YOLO
import torch
import easyocr

# -----------------------------
# Configuración básica
# -----------------------------
DEFAULT_WEIGHTS = (
    # Pesos YOLOv8 finetuneados para placas (Hugging Face).
    "https://huggingface.co/yasirfaizahmed/license-plate-object-detection/resolve/main/best.pt"
)
OUTPUT_DIR = "output_anpr"
CSV_PATH = os.path.join(OUTPUT_DIR, "logs", "placas.csv")
# Regex del formato colombiano: ABC-123 (acepta separador opcional -, espacio, punto o '·')
COL_PLATE_REGEX = re.compile(r"^[A-Z]{3}[\-\s\.\u00B7]?\d{3}$")

# En cuántos segundos consideramos "duplicada" la misma placa en la misma cámara
DUPLICATE_COOLDOWN_SEC = 3.0

# -----------------------------
# Utilidades
# -----------------------------
def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "logs"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "plates"), exist_ok=True)

def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def draw_label(img, text, x1, y1):
    cv2.putText(
        img,
        text,
        (int(x1), int(y1) - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )

def preprocess_for_ocr(plate_bgr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Devuelve (mejorado_bgr, bin_inv). Mejorado: CLAHE en L*a*b*, luego a gris.
    bin_inv: umbral adaptativo invertido (texto oscuro sobre fondo claro -> útil para OCR).
    """
    h = plate_bgr.shape[0]
    if h < 40:
        scale = 40.0 / max(h, 1)
        new_w = max(int(plate_bgr.shape[1] * scale), 1)
        plate_bgr = cv2.resize(plate_bgr, (new_w, 40), interpolation=cv2.INTER_LINEAR)

    lab = cv2.cvtColor(plate_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge([l2, a, b])
    enhanced_bgr = cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)

    gray = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    bin_inv = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 35, 15
    )
    return enhanced_bgr, bin_inv

def normalize_plate_text(raw_text: str) -> str:
    t = raw_text.upper()
    for ch in [" ", ".", "·", "_", "|", ":", "/"]:
        t = t.replace(ch, "")
    # Reinsertar guion para "ABC-123" si la longitud lo permite
    if len(t) >= 6:
        t = t[:3] + "-" + t[-3:]
    return t

def is_col_plate(text: str) -> bool:
    return COL_PLATE_REGEX.match(text) is not None

def save_plate_crop(cam_name: str, plate_text: str, frame_bgr: np.ndarray, box_xyxy: Tuple[int, int, int, int]) -> str:
    x1, y1, x2, y2 = [int(v) for v in box_xyxy]
    h, w = frame_bgr.shape[:2]
    x1 = max(0, min(x1, w - 1))
    y1 = max(0, min(y1, h - 1))
    x2 = max(0, min(x2, w - 1))
    y2 = max(0, min(y2, h - 1))
    crop = frame_bgr[y1:y2, x1:x2].copy()

    day_dir = os.path.join(OUTPUT_DIR, "plates", datetime.now().strftime("%Y%m%d"))
    os.makedirs(day_dir, exist_ok=True)
    safe_text = plate_text.replace("-", "")
    fname = f"{cam_name}_{safe_text}_{int(time.time())}.jpg"
    out_path = os.path.join(day_dir, fname)
    cv2.imwrite(out_path, crop)
    return out_path

def append_csv_row(row: List[str], lock: threading.Lock):
    header = ["timestamp", "camera", "plate", "det_conf", "ocr_conf", "file"]
    need_header = not os.path.exists(CSV_PATH)
    with lock:
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if need_header:
                writer.writerow(header)
            writer.writerow(row)

# Añade cerca de otras utils:

def is_yellow_plate(bgr, sat_thr=70, val_thr=80, min_ratio=0.20):
    """Valida que el recorte tenga suficiente amarillo (HSV).
    min_ratio=0.20 -> al menos 20% de pixeles 'amarillos' """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    # Rango de amarillo típico (ajustable según tu cámara/iluminación):
    # Hue 15-40 aprox. (OpenCV H: 0-179)
    lower = np.array([15, sat_thr, val_thr], dtype=np.uint8)
    upper = np.array([40, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)
    ratio = (mask > 0).mean()
    return ratio >= min_ratio

def plausible_aspect_ratio(w, h, min_ar=2.5, max_ar=6.5):
    """Placas colombianas usualmente apaisadas (ancho>>alto). Ajusta según tu cámara."""
    if h <= 0: return False
    ar = float(w) / float(h)
    return (min_ar <= ar <= max_ar)

def majority_vote(candidates):
    """candidates: lista de (text, ocr_conf). Devuelve (texto_modo, repeticiones, conf_media_del_modo)."""
    if not candidates:
        return None, 0, 0.0
    from collections import defaultdict
    counts = defaultdict(list)  # text -> [conf, conf, ...]
    for t, c in candidates:
        if t: counts[t].append(float(c))
    if not counts:
        return None, 0, 0.0
    best_text, best_list = max(counts.items(), key=lambda kv: len(kv[1]))
    return best_text, len(best_list), float(np.mean(best_list))


# -----------------------------
# OCR Wrapper
# -----------------------------
class PlateOCR:
    def __init__(self, use_gpu: bool):
        # Solo alfabeto y dígitos reduce errores (formato colombiano)
        self.reader = easyocr.Reader(
            ["en"], gpu=use_gpu
        )

    def read(self, plate_bgr: np.ndarray) -> Tuple[Optional[str], float]:
        enhanced_bgr, bin_inv = preprocess_for_ocr(plate_bgr)

        best_text = None
        best_conf = 0.0

        for img in [enhanced_bgr, bin_inv]:
            results = self.reader.readtext(
                img,
                detail=1,
                paragraph=False,
                allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-",
                # blocklist no se usa si allowlist está definido
            )
            if not results:
                continue

            # Ordenar por coordenada X media para unir textos de izquierda a derecha
            def x_center(item):
                (tl, tr, br, bl) = item[0]
                xs = [pt[0] for pt in [tl, tr, br, bl]]
                return float(sum(xs) / 4.0)

            results = sorted(results, key=x_center)
            raw = "".join([r[1] for r in results])
            text = normalize_plate_text(raw)
            conf_vals = [float(r[2]) for r in results if len(r) >= 3]
            conf = float(np.mean(conf_vals)) if conf_vals else 0.0

            if conf > best_conf:
                best_text = text
                best_conf = conf

        if best_text and is_col_plate(best_text):
            return best_text, best_conf
        return None, 0.0

# -----------------------------
# Trabajador de cámara (thread)
# -----------------------------
class CameraWorker(threading.Thread):
    def __init__(
        self,
        cam_name: str,
        source: str,
        model: YOLO,
        ocr: PlateOCR,
        csv_lock: threading.Lock,
        conf_thres: float,
        iou_thres: float,
        display: bool = True,
        args=None
        
    ):
        super().__init__(daemon=True)
        self.cam_name = cam_name
        self.source = source
        self.model = model
        self.ocr = ocr
        self.csv_lock = csv_lock
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.display = display
        self.args = args
        self.stop_event = threading.Event()
        self.last_seen = {}  # plate_text -> last_timestamp
        self.window = []  # ventana deslizante de OCR del frame actual [(text, conf)]
        self.lock_active = False
        self.lock_buffer = []  # acumula durante lock [(text, ocr_conf, det_conf, box, crop_bgr)]
        self.lock_frames_left = 0
        self.cooldown_until = 0.0  # evita commits muy seguidos

    def _should_cooldown(self):
        return time.time() < self.cooldown_until

    def stop(self):
        self.stop_event.set()

    def run(self):
        cap = cv2.VideoCapture(self._parse_source(self.source))
        if not cap.isOpened():
            print(f"[{self.cam_name}] No se pudo abrir la fuente: {self.source}")
            return

        window_name = f"ANPR - {self.cam_name}"
        if self.display:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print(f"[{self.cam_name}] Fin de stream o fallo de captura.")
                break

            # ... tras leer 'frame'
            results = self.model.predict(
                source=frame,
                conf=self.conf_thres,
                iou=self.iou_thres,
                verbose=False,
                device=0 if torch.cuda.is_available() else "cpu",
            )
            annotated = frame.copy()

            best_candidate = None  # (text, ocr_conf, det_conf, box, crop_bgr)

            if results and len(results) > 0:
                res = results[0]
                if res.boxes is not None and len(res.boxes) > 0:
                    # Tomamos la detección con mayor conf para estabilizar
                    idx = int(np.argmax(res.boxes.conf.cpu().numpy()))
                    box = res.boxes.xyxy[idx].cpu().numpy().astype(int)
                    det_conf = float(res.boxes.conf[idx].cpu().numpy())
                    x1, y1, x2, y2 = [int(v) for v in box]
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    crop = frame[y1:y2, x1:x2]

                    if crop.size > 0 and det_conf >= self.conf_thres and det_conf >= self.args.min_det:
                        # Chequeos visuales
                        h, w = crop.shape[:2]
                        ar_ok = plausible_aspect_ratio(w, h)
                        yellow_ok = True
                        if self.args.yellow_check:
                            yellow_ok = is_yellow_plate(crop)

                        plate_text, ocr_conf = (None, 0.0)
                        if ar_ok and yellow_ok:
                            plate_text, ocr_conf = self.ocr.read(crop)

                        label = f"d:{det_conf:.2f}"
                        if plate_text:
                            label = f"{plate_text} | d:{det_conf:.2f} o:{ocr_conf:.2f}"
                        draw_label(annotated, label, x1, y1)

                        if plate_text and ocr_conf >= self.args.min_ocr:
                            best_candidate = (plate_text, ocr_conf, det_conf, (x1,y1,x2,y2), crop, frame.copy())

            # --- CAPTURA MANUAL/HÍBRIDA (tecla 'c') ---
            manual_trigger = False
            if self.display:
                key = cv2.waitKey(1) & 0xFF
                if key == ord('c'):  # presionar 'c' para capturar
                    manual_trigger = True
                elif key == 27:
                    break
            else:
                key = -1

            # --- MODO LOCK & COMMIT ---
            if manual_trigger and best_candidate:
                # abre un lock corto tipo burst para elegir la mejor en ~self.args.lock_frames
                self.lock_active = True
                self.lock_frames_left = self.args.lock_frames
                self.lock_buffer = []

            if best_candidate:
                # ventana para consenso 'auto'
                self.window.append((best_candidate[0], best_candidate[1]))
                if len(self.window) > max(self.args.stable_frames * 2, 15):
                    self.window.pop(0)

                if self.lock_active:
                    self.lock_buffer.append(best_candidate)
                    self.lock_frames_left -= 1
                    if self.lock_frames_left <= 0:
                        # decidir 1 sola
                        text, reps, confm = majority_vote([(t,c) for (t,c,_,_,_) in self.lock_buffer])
                        if text and reps >= max(3, self.args.stable_frames//2):
                            if not self._should_cooldown():
                                # pick mejor crop por conf
                                best = max(self.lock_buffer, key=lambda x: (x[0]==text, x[1], x[2]))
                                best_frame = best[5]
                                file_path = save_plate_crop(self.cam_name, text, frame, best[3])
                                append_csv_row([now_iso(), self.cam_name, text,
                                                f"{best[2]:.3f}", f"{best[1]:.3f}", file_path], self.csv_lock)
                                self.cooldown_until = time.time() + DUPLICATE_COOLDOWN_SEC
                        self.lock_active = False
                        self.lock_buffer = []

                # AUTO (sin lock): si hay consenso en la ventana, guarda 1 vez
                text_win, rep_win, conf_win = majority_vote(self.window)
                if (self.args.capture_mode in ["auto","hybrid"] and
                    text_win and rep_win >= self.args.stable_frames and conf_win >= self.args.min_ocr and
                    not self._should_cooldown()):
                    # Guardar usando el candidato actual si coincide con el consenso
                    if best_candidate and best_candidate[0] == text_win:
                        file_path = save_plate_crop(self.cam_name, text_win, frame, best_candidate[3])
                        append_csv_row([now_iso(), self.cam_name, text_win,
                                        f"{best_candidate[2]:.3f}", f"{best_candidate[1]:.3f}", file_path], self.csv_lock)
                        self.cooldown_until = time.time() + DUPLICATE_COOLDOWN_SEC
                    # limpiar para no duplicar
                    self.window.clear()

            # Dibujar texto de ayuda si display
            if self.display:
                hud = f"[{self.cam_name}] 'c'=capturar | mode={self.args.capture_mode} | stable={self.args.stable_frames}"
                cv2.putText(annotated, hud, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 220, 20), 2, cv2.LINE_AA)
                cv2.imshow(window_name, annotated)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('c'):
                    manual_trigger = True
                elif key == 27:  # ESC
                    break
            else:
                key = -1

        cap.release()
        if self.display:
            cv2.destroyWindow(window_name)

    @staticmethod
    def _parse_source(s: str):
        # Si es un entero (índice de webcam), convertirlo
        try:
            idx = int(s)
            return idx
        except ValueError:
            return s




# -----------------------------
# Main
# -----------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="ANPR Colombia (YOLOv8 + EasyOCR)")
    parser.add_argument(
        "--cams",
        nargs="+",
        default=["0"],
        help="Lista de cámaras: índices (0 1 ...) o URLs (rtsp/http/archivo). Ej: --cams 0 1 rtsp://user:pass@ip/stream",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=DEFAULT_WEIGHTS,
        help="Ruta o URL de pesos YOLO (modelo de detección de placas).",
    )
    parser.add_argument("--conf", type=float, default=0.30, help="Confianza mínima detección YOLO.")
    parser.add_argument("--iou", type=float, default=0.50, help="IoU para NMS de YOLO.")
    parser.add_argument("--no-display", action="store_true", help="No mostrar ventanas (solo registrar).")
    # en parse_args()
    parser.add_argument("--capture-mode", choices=["auto", "manual", "hybrid"], default="auto",
        help="auto: guarda cuando hay estabilidad; manual: guarda sólo al presionar 'c'; hybrid: ambas.")
    parser.add_argument("--stable-frames", type=int, default=6,
        help="N mínimo de frames donde se repite la misma placa para considerarla estable.")
    parser.add_argument("--min-ocr", type=float, default=0.70,
        help="Confiabilidad OCR mínima (0-1) para validar una lectura.")
    parser.add_argument("--min-det", type=float, default=0.40,
        help="Confiabilidad YOLO mínima (0-1) para entrar a la ventana de consenso.")
    parser.add_argument("--yellow-check", action="store_true",
        help="Activa validación de fondo amarillo (reduce falsos positivos).")
    parser.add_argument("--lock-frames", type=int, default=12,
        help="Frames a acumular durante el lock antes de decidir y guardar 1 sola toma.")

    return parser.parse_args()

def main():
    ensure_dirs()
    args = parse_args()

    use_gpu = torch.cuda.is_available()
    print(f"GPU disponible: {use_gpu}")

    print(f"Cargando modelo YOLO desde: {args.weights}")
    model = YOLO(args.weights)

    print("Inicializando OCR (EasyOCR)...")
    ocr = PlateOCR(use_gpu=use_gpu)

    csv_lock = threading.Lock()
    workers: List[CameraWorker] = []
    display = not args.no_display

    # Lanzar un hilo por cámara
    for i, src in enumerate(args.cams):
        cam_name = f"cam{i}"
        w = CameraWorker(
            cam_name=cam_name,
            source=src,
            model=model,
            ocr=ocr,
            csv_lock=csv_lock,
            conf_thres=args.conf,
            iou_thres=args.iou,
            display=display,
            args=args
        )
        w.start()
        workers.append(w)

    print("Presiona Ctrl+C en consola para terminar.")
    try:
        while any(w.is_alive() for w in workers):
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("Finalizando...")
    finally:
        for w in workers:
            w.stop()
        for w in workers:
            w.join()

if __name__ == "__main__":
    main()
