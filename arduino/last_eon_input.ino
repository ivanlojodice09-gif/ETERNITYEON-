/*
  ETERNITYEON - Arduino input
  File: arduino/last_eon_input.ino

  Descrizione:
  - legge 3 input analogici
  - legge 1 valore di rumore/ampiezza
  - invia i dati sulla seriale in formato:
      0.1234,0.2345,0.3456,0.4567
  - ogni riga termina con \n

  Compatibile con Arduino Uno, Nano, Mega, ESP32.
*/

const int pinA = A0;
const int pinB = A1;
const int pinC = A2;
const int pinNoise = A3;

void setup() {
  Serial.begin(9600);
  delay(500);
  Serial.println("ETERNITYEON Arduino Ready");
}

void loop() {
  float sensorA = analogRead(pinA) / 1023.0;
  float sensorB = analogRead(pinB) / 1023.0;
  float sensorC = analogRead(pinC) / 1023.0;
  float noiseValue = analogRead(pinNoise) / 1023.0;

  Serial.print(sensorA, 4);
  Serial.print(",");
  Serial.print(sensorB, 4);
  Serial.print(",");
  Serial.print(sensorC, 4);
  Serial.print(",");
  Serial.println(noiseValue, 4);

  delay(50);
}