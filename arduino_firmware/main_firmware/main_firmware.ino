/**
 * AGRI-Scout Firmware v4.1 (English Standard)
 * Hardware: Arduino UNO + ESCs + 3 Ultrasonic Sensors
 * Logic: Smart Directional Blocking (Safety Shield)
 */

#include <Servo.h>

// --- SPEED CONFIGURATION (ESCs) ---
// 90 is neutral. Range is usually 0-180.
const int SPEED_STOP = 90;
const int SPEED_FWD_SLOW = 105;
const int SPEED_BACK_SLOW = 75;
const int SPEED_TURN_FWD = 110;
const int SPEED_TURN_BACK = 70;

// --- SAFETY CONFIGURATION ---
const int SAFE_DISTANCE_CM = 20;

// --- PIN DEFINITIONS (No conflicts with Motors) ---
// Motors (Must be PWM pins)
const int PIN_ESC_LEFT = 5;
const int PIN_ESC_RIGHT = 9;

// Sensors (Trigger / Echo)
const int TRIG_LEFT = 2;  const int ECHO_LEFT = 3;
const int TRIG_REAR = 4;  const int ECHO_REAR = 7;
const int TRIG_RIGHT = 8; const int ECHO_RIGHT = 11;

// Objects
Servo escLeft;
Servo escRight;

void setup() {
  Serial.begin(9600);

  // 1. Setup Sensors
  pinMode(TRIG_LEFT, OUTPUT); pinMode(ECHO_LEFT, INPUT);
  pinMode(TRIG_REAR, OUTPUT); pinMode(ECHO_REAR, INPUT);
  pinMode(TRIG_RIGHT, OUTPUT); pinMode(ECHO_RIGHT, INPUT);

  // 2. Setup Motors
  Serial.println("SYSTEM: Initializing ESCs...");
  escLeft.attach(PIN_ESC_LEFT);
  escRight.attach(PIN_ESC_RIGHT);
  
  // 3. Arming Sequence (Neutral Signal)
  stopMotors(); 
  delay(3000); // Wait 3s for ESCs to recognize neutral and stop beeping
  
  Serial.println("SYSTEM: Ready. 360 Shield Active.");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    executeCommand(cmd);
  }
}

// --- COMMAND LOGIC WITH PROTECTION ---
void executeCommand(char cmd) {
  
  // Read sensors BEFORE making a decision
  int distLeft = readDistance(TRIG_LEFT, ECHO_LEFT);
  int distRear = readDistance(TRIG_REAR, ECHO_REAR);
  int distRight = readDistance(TRIG_RIGHT, ECHO_RIGHT);

  switch (cmd) {
    case 'F': // Forward (We trust the user/camera, but could add Front Sensor here)
      moveForward();
      Serial.println("MOVING_FWD");
      break;

    case 'B': // Backward (Check REAR Sensor)
      if (distRear > SAFE_DISTANCE_CM) {
        moveBackward();
        Serial.println("MOVING_BACK");
      } else {
        stopMotors();
        Serial.println("WARNING: OBSTACLE_REAR");
      }
      break;

    case 'L': // Turn Left (Check LEFT Sensor)
      if (distLeft > SAFE_DISTANCE_CM) {
        turnLeft();
        Serial.println("TURNING_LEFT");
      } else {
        stopMotors();
        Serial.println("WARNING: OBSTACLE_LEFT");
      }
      break;

    case 'R': // Turn Right (Check RIGHT Sensor)
      if (distRight > SAFE_DISTANCE_CM) {
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
      
    case 'T': // Telemetry (Send data from all 3 sensors)
      Serial.print("DATA|Left:");
      Serial.print(distLeft);
      Serial.print("|Rear:");
      Serial.print(distRear);
      Serial.print("|Right:");
      Serial.println(distRight);
      break;
  }
}

// --- MOVEMENT FUNCTIONS ---
void moveForward() {
  escLeft.write(SPEED_FWD_SLOW);
  escRight.write(SPEED_FWD_SLOW);
}

void moveBackward() {
  escLeft.write(SPEED_BACK_SLOW);
  escRight.write(SPEED_BACK_SLOW);
}

void turnLeft() {
  // Tank Turn: Left goes Back, Right goes Forward
  escLeft.write(SPEED_TURN_BACK);
  escRight.write(SPEED_TURN_FWD);
}

void turnRight() {
  // Tank Turn: Left goes Forward, Right goes Back
  escLeft.write(SPEED_TURN_FWD);
  escRight.write(SPEED_TURN_BACK);
}

void stopMotors() {
  escLeft.write(SPEED_STOP);
  escRight.write(SPEED_STOP);
}

// --- HELPER FUNCTION ---
int readDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW); delayMicroseconds(2);
  digitalWrite(trigPin, HIGH); delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // Short timeout (25ms) to prevent blocking the robot loop
  long duration = pulseIn(echoPin, HIGH, 25000); 
  
  if (duration == 0) return 999; // No obstacle (infinity)
  return duration * 0.034 / 2;
}