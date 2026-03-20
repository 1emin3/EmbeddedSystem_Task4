#include <Arduino.h>

int xPin = A0;
int yPin = A1;

int upLed = 10;
int downLed = 9;
int leftLed = 11;
int rightLed = 6;

int centerMin = 430;
int centerMax = 590;

void setup() {
  Serial.begin(9600);

  pinMode(upLed, OUTPUT);
  pinMode(downLed, OUTPUT);
  pinMode(leftLed, OUTPUT);
  pinMode(rightLed, OUTPUT);
}

void loop() {
  int xVal = analogRead(xPin);
  int yVal = analogRead(yPin);

  String direction = "CENTER";

  // Turn off all LEDs first
  digitalWrite(upLed, LOW);
  digitalWrite(downLed, LOW);
  digitalWrite(leftLed, LOW);
  digitalWrite(rightLed, LOW);

  // Direction logic
  if (yVal > centerMax) {
    direction = "UP";
    digitalWrite(upLed, HIGH);
  }
  else if (yVal < centerMin) {
    direction = "DOWN";
    digitalWrite(downLed, HIGH);
  }
  else if (xVal < centerMin) {
    direction = "LEFT";
    digitalWrite(leftLed, HIGH);
  }
  else if (xVal > centerMax) {
    direction = "RIGHT";
    digitalWrite(rightLed, HIGH);
  }

  // Send data to GUI
  Serial.print("x=");
  Serial.print(xVal);
  Serial.print(",y=");
  Serial.print(yVal);
  Serial.print(",dir=");
  Serial.println(direction);

  delay(50);
}