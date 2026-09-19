const int ledPin = 9; // Pin con soporte PWM

void setup() {
  Serial.begin(9600); // Iniciar comunicación serial a 9600 baudios
  pinMode(ledPin, OUTPUT);
}

void loop() {
  // Verificar si hay datos provenientes de Python
  if (Serial.available() > 0) {
    // Leer un solo byte (valores de 0 a 255)
    int brightness = Serial.read(); 
    
    // Aplicar el valor PWM al LED
    analogWrite(ledPin, brightness);
  }
}