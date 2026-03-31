#include <Servo.h>
#include <Stepper.h>

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

// ESC Parameters / Boundaries
const int ESC_NEUTRAL = 90;
const int ESC_MIN = 0;
const int ESC_MAX = 180;

// ==========================================
// 3. FAILSAFE & STATE TRACKING
// ==========================================
unsigned long lastCommandTime = 0;
const unsigned long FAILSAFE_TIMEOUT_MS =
    1000; // Stops motors if no command in 1000ms
bool isStopped = true;

// Probe State Machine for non-blocking continuous movement
enum ProbeState { PROBE_STOP, PROBE_UP, PROBE_DOWN };
ProbeState currentProbeState = PROBE_STOP;

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
  probeStepper.setSpeed(50);

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

    // Skip trailing whitespace or random characters
    if (commandType == '\n' || commandType == '\r' || commandType == ' ') {
      return;
    }

    lastCommandTime = millis(); // Refresh the failsafe timer

    // Command 'S': Fixed steps block (Legacy compatibility)
    if (commandType == 'S') {
      int steps = Serial.parseInt();
      moveProbe(steps);
      currentProbeState = PROBE_STOP;
    }

    // Command 'U': Start moving Probe UP continuously
    else if (commandType == 'U') {
      currentProbeState = PROBE_UP;
      Serial.println("Probe -> Moving UP.");
    }

    // Command 'D': Start moving Probe DOWN continuously
    else if (commandType == 'D') {
      currentProbeState = PROBE_DOWN;
      Serial.println("Probe -> Moving DOWN.");
    }

    // Command 'F': Forward (Frente)
    // Invertido fisicamente: agora subtrai para ir para frente
    else if (commandType == 'F') {
      int speed = Serial.parseInt();
      moveDirection(-speed, -speed);
      isStopped = false;
    }

    // Command 'B': Backward (Trás)
    // Invertido fisicamente: agora soma para ir para trás
    else if (commandType == 'B') {
      int speed = Serial.parseInt();
      moveDirection(speed, speed);
      isStopped = false;
    }

    // Command 'L': Left (Esquerda - Skid steer mapping)
    else if (commandType == 'L') {
      int speed = Serial.parseInt();
      moveDirection(speed, -speed);
      isStopped = false;
    }

    // Command 'R': Right (Direita - Skid steer mapping)
    else if (commandType == 'R') {
      int speed = Serial.parseInt();
      moveDirection(-speed, speed);
      isStopped = false;
    }

    // Command 'X': Hard Stop (Parar Tudo)
    else if (commandType == 'X') {
      stopWheels();
      currentProbeState = PROBE_STOP;
      Serial.println("SYSTEM HALTED: Wheels and Probe stopped.");
    }
  }

  // --- Failsafe Watchdog Routine ---
  // If the robot hasn't received any command from the Raspberry Pi
  // within the timeout limit, stop everything safely.
  if (millis() - lastCommandTime > FAILSAFE_TIMEOUT_MS) {
    if (!isStopped || currentProbeState != PROBE_STOP) {
      Serial.println("WARNING: Communication Timeout. Engaging failsafe (All "
                     "Motors Stopped).");
      stopWheels();
      currentProbeState = PROBE_STOP;
    }
  }

  // --- Probe Continuous Movement Task ---
  // This gives non-blocking step control
  if (currentProbeState == PROBE_UP) {
    probeStepper.step(
        1); // Needs testing for actual physical polarity (Up vs Down)
  } else if (currentProbeState == PROBE_DOWN) {
    probeStepper.step(-1);
  }
}

// ==========================================
// FUNCTIONS
// ==========================================

// Legacy blocking function
void moveProbe(int steps) {
  Serial.print("Moving probe by steps: ");
  Serial.println(steps);
  probeStepper.step(steps);
  Serial.println("Probe movement complete.");
}

// Wrapper to map relative intensities (-90 to +90) to ESC absolute PWM (0 to
// 180)
void moveDirection(int leftRelative, int rightRelative) {
  int leftPWM = ESC_NEUTRAL + leftRelative;
  int rightPWM = ESC_NEUTRAL + rightRelative;
  driveWheels(leftPWM, rightPWM);
}

// Core function to control the skid-steering wheels robustly
void driveWheels(int leftPWM, int rightPWM) {
  // Always limit values explicitly to prevent hardware glitches (constrain to
  // 0-180)
  leftPWM = constrain(leftPWM, ESC_MIN, ESC_MAX);
  rightPWM = constrain(rightPWM, ESC_MIN, ESC_MAX);

  leftESC.write(leftPWM);
  rightESC.write(rightPWM);

  Serial.print("Wheels -> L: ");
  Serial.print(leftPWM);
  Serial.print(" R: ");
  Serial.println(rightPWM);
}

// Function to safely stop the vehicle wheels
void stopWheels() {
  leftESC.write(ESC_NEUTRAL);
  rightESC.write(ESC_NEUTRAL);
  isStopped = true;
}
