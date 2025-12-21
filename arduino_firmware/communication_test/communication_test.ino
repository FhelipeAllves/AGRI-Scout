// --- ARDUINO CODE ---
// This code turns the Arduino into a serial "listener".

const int ledPin = 13; // Built-in LED on most Arduinos 

void setup() {
  Serial.begin(9600); // Starts serial communication at 9600 baud
  pinMode(ledPin, OUTPUT);
  
  // Blink twice quickly to indicate Arduino startup/reset
  digitalWrite(ledPin, HIGH); delay(100);
  digitalWrite(ledPin, LOW);  delay(100);
  digitalWrite(ledPin, HIGH); delay(100);
  digitalWrite(ledPin, LOW);
}

void loop() {
  // 1. Check if any data has arrived from the Raspberry Pi
  if (Serial.available() > 0) {
    
    // 2. Read the incoming character
    char command = Serial.read(); 

    // 3. Decide what to do
    if (command == 'L') { 
      digitalWrite(ledPin, HIGH); // Turn LED ON
      // 4. Send feedback to the Pi
      Serial.println("Arduino: LED turned ON successfully!"); 
    }
    
    else if (command == 'D') {
      digitalWrite(ledPin, LOW); // Turn LED OFF
      Serial.println("Arduino: LED turned OFF.");
    }
    
    else {
      // Any other character
      Serial.println("Arduino: Command not recognized.");
    }
  }
}
