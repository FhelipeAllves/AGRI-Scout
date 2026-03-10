#include <Stepper.h>
#include <Servo.h>

// ==========================================
// 1. STEPPER MOTOR CONFIGURATION (PROBE)
// ==========================================
const int stepsPerRevolution = 200;

// Pins for DFRobot L298N Black Edition
const int pinM1 = 4; // Direction Motor 1
const int pinE1 = 5; // Enable Motor 1
const int pinE2 = 6; // Enable Motor 2
const int pinM2 = 7; // Direction Motor 2

// Initialize stepper using only direction pins (M1, M2)
Stepper probeStepper(stepsPerRevolution, pinM1, pinM2);


// ==========================================
// 2. ESC CONFIGURATION (WHEELS)
// ==========================================
const int leftEscPin = 9;
const int rightEscPin = 10;

Servo leftESC;
Servo rightESC;


// ==========================================
// SETUP ROUTINE
// ==========================================
void setup() {
  Serial.begin(9600);
  Serial.setTimeout(10);

  // --- Setup Stepper ---
  pinMode(pinE1, OUTPUT);
  pinMode(pinE2, OUTPUT);
  
  // Keep the Enable pins HIGH so the driver maintains holding torque
  digitalWrite(pinE1, HIGH);
  digitalWrite(pinE2, HIGH);
  
  // Low speed for high torque when digging into the soil
  probeStepper.setSpeed(30); 

  // --- Setup ESCs ---
  leftESC.attach(leftEscPin);
  rightESC.attach(rightEscPin);

  // Send neutral signal to initialize ESCs safely
  stopWheels();

  Serial.println("System Initialized. Awaiting commands from Raspberry Pi.");
}


// ==========================================
// MAIN LOOP: COMMAND PARSER
// ==========================================
void loop() {
  // Check if Raspberry Pi sent a command via USB
  if (Serial.available() > 0) {
    char commandType = Serial.read();

    // Command 'S': Move the probe (Stepper)
    // Example from Pi: S200 (moves 1 revolution down)
    if (commandType == 'S') {
      int steps = Serial.parseInt();
      moveProbe(steps);
    }
    
    // Command 'W': Move the wheels (ESCs)
    // Example from Pi: W110 110 (moves both sides forward)
    else if (commandType == 'W') {
      int leftSpeed = Serial.parseInt();
      int rightSpeed = Serial.parseInt();
      driveWheels(leftSpeed, rightSpeed);
    }
  }
}


// ==========================================
// FUNCTIONS
// ==========================================

// Function to move the soil probe
void moveProbe(int steps) {
  Serial.print("Moving probe by steps: ");
  Serial.println(steps);
  
  probeStepper.step(steps);
  
  Serial.println("Probe movement complete.");
}

// Function to control the skid-steering wheels
void driveWheels(int leftSpeed, int rightSpeed) {
  // ESCs typically expect values from 0 to 180. 
  // 90 is neutral/stop. < 90 is reverse. > 90 is forward.
  leftESC.write(leftSpeed);
  rightESC.write(rightSpeed);
  
  Serial.print("Wheels updated -> L: ");
  Serial.print(leftSpeed);
  Serial.print(" R: ");
  Serial.println(rightSpeed);
}

// Function to safely stop the vehicle
void stopWheels() {
  leftESC.write(90); // 90 degrees equals 1500us (neutral PWM)
  rightESC.write(90);
}