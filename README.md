# Control de brillo de un LED (PWM) con la mano y la cámara

Con la cámara web y Python detectamos tu mano. La distancia entre la punta del **pulgar** y la del **índice** controla el brillo de un LED conectado a un Arduino:

- Dedos juntos → LED apagado
- Dedos separados → LED al máximo

Usa **MediaPipe** (detección de manos), **OpenCV** (cámara) y **pyserial** (comunicación con Arduino).

## Qué necesitas

- Arduino (Uno, Nano o similar) con cable USB
- 1 LED + 1 resistencia de 220 Ω
- Cámara web (o la de la laptop)
- Python 3.10 o superior
- Internet la primera vez (se descarga el modelo de manos)

## 1. Conectar el circuito

| Arduino | Componente |
|---------|------------|
| Pin 9 (PWM) | Resistencia 220 Ω → pata larga (+) del LED |
| GND | Pata corta (–) del LED |

> Si usas otro pin, debe ser uno con PWM (marcado con `~`) y debes cambiarlo en el sketch.

## 2. Cargar el código en el Arduino

Abre el Arduino IDE, pega este sketch y súbelo a la placa:

```cpp
const int LED_PIN = 9;

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    int brillo = Serial.read();   // valor de 0 a 255
    analogWrite(LED_PIN, brillo);
  }
}
```

Después **cierra el Monitor Serie** del Arduino IDE. Si queda abierto, ocupa el puerto y Python no podrá conectarse.

## 3. Descargar el proyecto

```powershell
git clone https://github.com/Jonixmax/pwm-con-camara-y-python.git
cd pwm-con-camara-y-python
```

## 4. Crear el entorno e instalar dependencias

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install opencv-python mediapipe pyserial numpy
```

> Instala **`pyserial`**, no `serial`. Son paquetes distintos y el segundo da error.

## 5. Configurar el puerto COM

Abre `led.py` y cambia esta línea por el puerto de tu Arduino:

```python
puerto_arduino = 'COM3'
```

Para saber cuál es: en el Arduino IDE ve a *Herramientas → Puerto*, o abre el *Administrador de dispositivos → Puertos (COM y LPT)*.

## 6. Ejecutar

```powershell
.\.venv\Scripts\python.exe led.py
```

La primera vez descargará el archivo `hand_landmarker.task` (unos MB). Después muestra la cámara: pon la mano frente a ella y junta o separa el pulgar y el índice. Presiona **ESC** para salir.

## Problemas comunes

| Problema | Solución |
|----------|----------|
| `Error serial: could not open port 'COM3'` | El puerto es otro, o el Monitor Serie / otro programa lo está usando |
| La ventana no abre o sale en negro | Cambia `cv2.VideoCapture(0)` por `cv2.VideoCapture(1, cv2.CAP_DSHOW)` |
| Cámara bloqueada | Windows → Configuración → Privacidad y seguridad → Cámara, y cierra Zoom/Teams/OBS |
| El LED no llega al máximo o no se apaga | Ajusta el rango `[30, 200]` en `np.interp(...)` según qué tan lejos estés de la cámara |
| `No module named 'serial'` | Ejecuta `pip install pyserial` dentro del entorno |
| El Arduino se reinicia al abrir el script | Es normal: al conectarse por serial la placa se reinicia (por eso el script espera 2 s) |

## Cómo funciona

1. OpenCV captura cada fotograma de la cámara.
2. MediaPipe detecta la mano y devuelve 21 puntos; usamos el 4 (pulgar) y el 8 (índice).
3. Se calcula la distancia en píxeles entre ambos puntos.
4. Esa distancia se convierte al rango 0–255 y se envía como un byte por serial.
5. El Arduino lo recibe y lo aplica al LED con `analogWrite()` (PWM).
