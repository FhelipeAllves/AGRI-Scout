/**
 * AGRI-Scout Firmware v5.0 (Robust Checksum + DC RC-Driver)
 */

#include <Servo.h>
#include <Stepper.h>

// ==========================================
// 1. STEPPER MOTOR CONFIGURATION (PROBE)
// ==========================================
const int STEPS_PER_REVOLUTION = 200;
const int pinM1 = 4; // Direction Motor 1
const int pinE1 = 5; // Enable Motor 1
const int pinE2 = 6; // Enable Motor 2
const int pinM2 = 7; // Direction Motor 2

/// Global variable to track the last direction (add at the top of the code)
char lastMoveCmd = 'X';

Stepper probeStepper(STEPS_PER_REVOLUTION, pinM1, pinM2);

// Probe State Machine
enum ProbeState { PROBE_STOP, PROBE_UP, PROBE_DOWN };
ProbeState currentProbeState = PROBE_STOP;

// ==========================================
// 2. RC DRIVER CONFIGURATION (WHEELS)
// ==========================================
const int PIN_ESC_LEFT = 9;
const int PIN_ESC_RIGHT = 10;

Servo leftESC;
Servo rightESC;

const int ESC_NEUTRAL = 90;
const int ESC_MIN = 0;
const int ESC_MAX = 180;

// ==========================================
// 3. COMMUNICATION & FAILSAFE
// ==========================================
const byte START_BYTE = 0x3C; // '<'
const byte END_BYTE = 0x3E;   // '>'

unsigned long lastCommandTime = 0;
const unsigned long FAILSAFE_TIMEOUT_MS = 1000;
bool isStopped = true;

bool newData = false;
byte receivedCommand = 0;
byte receivedValue = 0;

void setup() {
  Serial.begin(9600);

  // Stepper Setup
  pinMode(pinE1, OUTPUT);
  pinMode(pinE2, OUTPUT);
  digitalWrite(pinE1, HIGH);
  digitalWrite(pinE2, HIGH);
  probeStepper.setSpeed(50);

  // Wheels Setup
  leftESC.attach(PIN_ESC_LEFT);
  rightESC.attach(PIN_ESC_RIGHT);
  stopWheels();

  Serial.println("SYSTEM: Initialized. Robust Protocol Active.");
}

void loop() {
  receiveSecurePacket();

  if (newData) {
    executeCommand((char)receivedCommand, (int)receivedValue);
    newData = false;
  }

  // Watchdog Failsafe
  if (millis() - lastCommandTime > FAILSAFE_TIMEOUT_MS) {
    if (!isStopped || currentProbeState != PROBE_STOP) {
      Serial.println("WARNING: Timeout! Engaging Failsafe.");
      stopWheels();
      currentProbeState = PROBE_STOP;
    }
  }

  // Non-blocking Probe Movement
  if (currentProbeState == PROBE_UP) {
    probeStepper.step(1);
  } else if (currentProbeState == PROBE_DOWN) {
    probeStepper.step(-1);
  }
}

// --- PACKET PARSER ---
void receiveSecurePacket() {
  static boolean recvInProgress = false;
  static byte index = 0;
  byte incomingByte;
  static byte packetBuffer[3];

  while (Serial.available() > 0 && newData == false) {
    incomingByte = Serial.read();

    if (recvInProgress == true) {
      if (incomingByte != END_BYTE) {
        packetBuffer[index] = incomingByte;
        index++;
        if (index >= 3)
          index = 2; // Prevent overflow
      } else {
        recvInProgress = false;
        index = 0;

        byte cmd = packetBuffer[0];
        byte val = packetBuffer[1];
        byte rx_checksum = packetBuffer[2];

        // Verify Integrity
        if ((cmd ^ val) == rx_checksum) {
          receivedCommand = cmd;
          receivedValue = val;
          newData = true;
          lastCommandTime = millis(); // Refresh Watchdog
        }
      }
    } else if (incomingByte == START_BYTE) {
      recvInProgress = true;
    }
  }
}

void executeCommand(char cmd, int speed) {

  // --- THE "AUTO-SPACE" LOGIC ---
  // If the command is a movement, AND it's different from the last one, AND we
  // aren't already stopped
  if ((cmd == 'F' || cmd == 'B' || cmd == 'L' || cmd == 'R') &&
      (cmd != lastMoveCmd && lastMoveCmd != 'X')) {

    Serial.println("SYSTEM: AUTO-SPACE (BRAKE INITIATED)");
    stopWheels(); // Force Neutral (90)

    // Mimic the human delay of pressing the Spacebar
    delay(2 * 500);

    // CRITICAL FIX: Clear the Serial buffer.
    // The Pi kept sending packets while we were waiting 500ms.
    // We must flush them to avoid confusing the ESC with queued commands.
    while (Serial.available() > 0) {
      Serial.read();
    }

    newData = false;
    lastMoveCmd = 'X'; // Reset state to Neutral
  }

  // Update the tracker for the next cycle
  lastMoveCmd = cmd;

  // --- NORMAL COMMAND EXECUTION ---
  switch (cmd) {
  case 'F':
    moveDirection(-speed, -speed);
    Serial.println("MOVING: FWD");
    break;
  case 'B':
    moveDirection(speed, speed);
    Serial.println("MOVING: BACK");
    break;
  case 'L':
    moveDirection(speed, -speed);
    Serial.println("TURNING: LEFT");
    break;
  case 'R':
    moveDirection(-speed, speed);
    Serial.println("TURNING: RIGHT");
    break;
  case 'U':
    currentProbeState = PROBE_UP;
    Serial.println("PROBE: UP");
    break;
  case 'D':
    currentProbeState = PROBE_DOWN;
    Serial.println("PROBE: DOWN");
    break;
  case 'X':
    stopWheels();
    currentProbeState = PROBE_STOP;
    lastMoveCmd = 'X';
    Serial.println("SYSTEM: STOPPED");
    break;
  }
}

// --- WHEEL MATH (Based on User's working model) ---
void moveDirection(int leftRelative, int rightRelative) {
  int leftPWM = constrain(ESC_NEUTRAL + leftRelative, ESC_MIN, ESC_MAX);
  int rightPWM = constrain(ESC_NEUTRAL + rightRelative, ESC_MIN, ESC_MAX);

  leftESC.write(leftPWM);
  rightESC.write(rightPWM);
  isStopped = false;
}

void stopWheels() {
  leftESC.write(ESC_NEUTRAL);
  rightESC.write(ESC_NEUTRAL);
  isStopped = true;
}