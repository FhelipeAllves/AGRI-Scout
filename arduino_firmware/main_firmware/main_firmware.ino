/**
 * AGRI-Scout Firmware v2.0
 * Authors: Pedro Alves & Luiz Felipe
 * * Description: 
 * Controls DC motors via Serial commands and handles obstacle avoidance
 * using 3 Ultrasonic Sensors (Left, Rear, Right).
 */

// --- CONFIGURATION ---
const int SAFE_DISTANCE_CM = 20; // Minimum distance to allow movement

// --- PIN DEFINITIONS ---
// Ultrasonic Sensors
const int TRIG_LEFT = 2;
const int ECHO_LEFT = 3;

const int TRIG_REAR = 4;
const int ECHO_REAR = 5;

const int TRIG_RIGHT = 6;
const int ECHO_RIGHT = 7;

// Motors (Check your driver wiring)
// Motor A (Left)
const int IN1 = 5;
const int IN2 = 6;
// Motor B (Right)
const int IN3 = 9;
const int IN4 = 10;

void setup() {
  // Initialize Serial Communication with Raspberry Pi
  Serial.begin(9600);

  // Initialize Motor Pins
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);

  // Initialize Sensor Pins
  pinMode(TRIG_LEFT, OUTPUT); pinMode(ECHO_LEFT, INPUT);
  pinMode(TRIG_REAR, OUTPUT); pinMode(ECHO_REAR, INPUT);
  pinMode(TRIG_RIGHT, OUTPUT); pinMode(ECHO_RIGHT, INPUT);

  stopMotors(); // Safety first
  Serial.println("Arduino Ready. Safety System Active.");
}

void loop() {
  // Check for incoming commands from Raspberry Pi
  if (Serial.available() > 0) {
    char command = Serial.read();
    handleCommand(command);
  }
}

// --- COMMAND HANDLER ---
void handleCommand(char cmd) {
  // We check sensors BEFORE moving. This creates a "Reflex".
  
  switch (cmd) {
    case 'F': // Forward
      // Usually we have a camera in front, so we trust the Pi.
      // But if you add a Front Sensor, check it here.
      moveForward();
      Serial.println("MOVING_FWD");
      break;

    case 'B': // Backward
      if (getDistance(TRIG_REAR, ECHO_REAR) > SAFE_DISTANCE_CM) {
        moveBackward();
        Serial.println("MOVING_BACK");
      } else {
        stopMotors();
        Serial.println("WARNING: OBSTACLE_REAR");
      }
      break;

    case 'L': // Left Turn
      // Check Left Sensor before turning
      if (getDistance(TRIG_LEFT, ECHO_LEFT) > SAFE_DISTANCE_CM) {
        turnLeft();
        Serial.println("TURNING_LEFT");
      } else {
        stopMotors();
        Serial.println("WARNING: OBSTACLE_LEFT");
      }
      break;

    case 'R': // Right Turn
      // Check Right Sensor before turning
      if (getDistance(TRIG_RIGHT, ECHO_RIGHT) > SAFE_DISTANCE_CM) {
        turnRight();
        Serial.println("TURNING_RIGHT");
      } else {
        stopMotors();
        Serial.println("WARNING: OBSTACLE_RIGHT");
      }
      break;

    case 'S': // Stop
    case 'P': 
      stopMotors();
      Serial.println("STOPPED");
      break;
      
    case 'T': // Test Sensors (Telemetry Request)
      sendTelemetry();
      break;
  }
}

// --- SENSOR HELPER ---
int getDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000); // 30ms timeout (approx 5 meters)
  
  if (duration == 0) return 999; // No echo = clear path (or error)
  
  return duration * 0.034 / 2; // Convert to cm
}

void sendTelemetry() {
  int dLeft = getDistance(TRIG_LEFT, ECHO_LEFT);
  delay(5);
  int dRear = getDistance(TRIG_REAR, ECHO_REAR);
  delay(5);
  int dRight = getDistance(TRIG_RIGHT, ECHO_RIGHT);

  Serial.print("DATA|L:");
  Serial.print(dLeft);
  Serial.print("|R:");
  Serial.print(dRear);
  Serial.print("|R:");
  Serial.println(dRight);
}

// --- MOTOR FUNCTIONS ---
void moveForward() {
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void moveBackward() {
  digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
}

void turnLeft() {
  digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void turnRight() {
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
}

void stopMotors() {
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
}