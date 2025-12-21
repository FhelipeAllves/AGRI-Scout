# AGRI-Scout 🚜
**Autonomous Agricultural Inspection Robot**

**Authors:** Pedro Alves & Luiz Felipe

---

## About the Project
AGRI-Scout is a 4WD mobile robot designed for precision agriculture. It combines computer vision for navigation with a specialized probe mechanism to analyze soil properties (NPK, pH, Moisture) in real-time.

The system uses a **Raspberry Pi 4** for high-level logic and vision, connected to an **Arduino** that controls motors and sensors.

## Key Features
* **Autonomous Navigation:** Follows crop lines using a camera and avoids obstacles with ultrasonic sensors.
* **Soil Analysis:** Automatically inserts a probe into the ground to read soil data.
* **Smart Monitoring:** Measures Nitrogen, Phosphorus, Potassium, pH, and Temperature.

## Hardware Stack
* **Main Computer:** Raspberry Pi 4 Model B (Ubuntu)
* **Microcontroller:** Arduino Uno / Mega
* **Sensors:**
  * Logitech USB Webcam
  * 3x HC-SR04 Ultrasonic Sensors
  * 8-in-1 RS485 Soil Sensor
* **Power:** LiPo Battery + Traco Power Regulation
