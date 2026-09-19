import os
import time
import math
import urllib.request

import cv2
import serial
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# --- CONFIGURACIÓN DEL SERIAL ---
puerto_arduino = 'COM3'  # <-- CAMBIA ESTO POR TU PUERTO
baudios = 9600

try:
    arduino = serial.Serial(puerto_arduino, baudios, timeout=1)
    time.sleep(2)
    print("Conexión serial establecida.")
except Exception as e:
    print(f"Error serial: {e}")
    exit()

# --- DESCARGAR EL MODELO DE MANOS (solo la primera vez) ---
MODELO = "hand_landmarker.task"
URL_MODELO = ("https://storage.googleapis.com/mediapipe-models/"
              "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")

if not os.path.exists(MODELO):
    print("Descargando modelo de manos (solo la primera vez)...")
    urllib.request.urlretrieve(URL_MODELO, MODELO)
    print("Modelo descargado.")

# --- CONFIGURACIÓN DE MEDIAPIPE (API nueva) ---
opciones = vision.HandLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path=MODELO),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7,
)
detector = vision.HandLandmarker.create_from_options(opciones)

# Conexiones entre los 21 puntos de la mano (para dibujar el esqueleto)
CONEXIONES = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # pulgar
    (0, 5), (5, 6), (6, 7), (7, 8),          # índice
    (5, 9), (9, 10), (10, 11), (11, 12),     # medio
    (9, 13), (13, 14), (14, 15), (15, 16),   # anular
    (13, 17), (17, 18), (18, 19), (19, 20),  # meñique
    (0, 17),                                  # palma
]

# --- INICIAR LA CÁMARA ---
cap = cv2.VideoCapture(0)  # 0 es la cámara por defecto de tu PC

print("Presiona la tecla 'ESC' en la ventana del video para salir.")

inicio = time.time()

while cap.isOpened():
    exito, fotograma = cap.read()
    if not exito:
        break

    # Voltear la imagen como un espejo
    fotograma = cv2.flip(fotograma, 1)
    alto, ancho, _ = fotograma.shape

    # MediaPipe necesita RGB
    fotograma_rgb = cv2.cvtColor(fotograma, cv2.COLOR_BGR2RGB)
    imagen_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=fotograma_rgb)

    # El modo VIDEO exige una marca de tiempo en milisegundos que siempre aumente
    marca_tiempo = int((time.time() - inicio) * 1000)
    resultados = detector.detect_for_video(imagen_mp, marca_tiempo)

    if resultados.hand_landmarks:
        for puntos_mano in resultados.hand_landmarks:
            # Convertir todos los puntos a coordenadas de píxeles
            pts = [(int(p.x * ancho), int(p.y * alto)) for p in puntos_mano]

            # Dibujar el esqueleto de la mano
            for a, b in CONEXIONES:
                cv2.line(fotograma, pts[a], pts[b], (255, 255, 255), 2)
            for p in pts:
                cv2.circle(fotograma, p, 4, (0, 0, 255), cv2.FILLED)

            # Punto 4 = punta del pulgar, punto 8 = punta del índice
            x1, y1 = pts[4]
            x2, y2 = pts[8]

            cv2.circle(fotograma, (x1, y1), 10, (255, 0, 0), cv2.FILLED)  # Pulgar
            cv2.circle(fotograma, (x2, y2), 10, (255, 0, 0), cv2.FILLED)  # Índice
            cv2.line(fotograma, (x1, y1), (x2, y2), (0, 255, 0), 3)       # Línea verde

            # Distancia entre ambos dedos
            distancia = math.hypot(x2 - x1, y2 - y1)

            # Convertir distancia al rango de brillo (0 a 255)
            # 30 = dedos casi juntos, 200 = dedos separados. Ajusta según tu distancia a la cámara.
            brillo_int = int(np.interp(distancia, [30, 200], [0, 255]))

            # Enviar el valor al Arduino
            arduino.write(bytes([brillo_int]))

            cv2.putText(fotograma, f'Brillo: {brillo_int}', (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow('Control LED con Dedos', fotograma)

    # Salir con ESC
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Limpieza y apagado
arduino.write(bytes([0]))  # Apagar el LED antes de salir
arduino.close()
detector.close()
cap.release()
cv2.destroyAllWindows()