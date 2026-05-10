# Hardware Tests - AGRI-Scout (Physical Robot)

Welcome to the testing toolkit for the physical AGRI-Scout.
These scripts are designed to independently verify each sensor, motor, and the system running ROS 2 (Raspberry Pi 4 B + Arduino), ensuring everything is ready before bringing up the autonomous navigation stack (`nav2`).

This step-by-step guide is designed to walk you through everything from connecting to the internet to running the tests. Follow the steps chronologically.

---

## Step 0: Basic Access and Internet on the Raspberry Pi

If you have powered on the Raspberry Pi and are unsure if it is connected to the internet:

### 1. Connecting the Raspberry Pi to the Internet (Wi-Fi)
If using the Raspberry Pi with a monitor and keyboard, you can connect to Wi-Fi using the OS graphical interface (top right corner).

If accessing via command line (terminal, SSH, or TTY), use the `nmcli` network manager:
```bash
# List available Wi-Fi networks
nmcli dev wifi list

# Connect to your network (replace with your network name and password)
sudo nmcli dev wifi connect "NETWORK_NAME" password "YOUR_WIFI_PASSWORD"
```

### 2. Testing the connection
```bash
ping -c 4 google.com
```
*If the command replies with "64 bytes from...", you have internet access and can proceed! If you get a network error, repeat Step 1.*

---

## Step 1: Verifying and Preparing the Environment (ROS 2)

The robot's brain uses **ROS 2 Jazzy**. We must ensure it is installed and the project workspace (`agri_scout_ws` directory) is ready.

### 1. Is ROS 2 installed?
To check if ROS 2 is installed, try to "source" its environment in the current terminal:
```bash
source /opt/ros/jazzy/setup.bash
```
* **If NOTHING appears on the screen:** The command succeeded, ROS 2 is installed!
* **If you get an error (e.g., `No such file or directory`):** ROS 2 is not installed. Follow the [official ROS 2 Jazzy Ubuntu installation documentation](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html) (download the "Desktop" packages) before proceeding.

### 2. Does the Workspace (`agri_scout_ws`) exist and is it compiled?
The robot's navigation code and packages are located in the `~/agri_scout_ws` workspace.
Check if it has been compiled and is ready for use by listing the install directory:
```bash
ls ~/agri_scout_ws/install
```
* **If the folder exists:** Great! Source the workspace setup:
  ```bash
  source ~/agri_scout_ws/install/setup.bash
  ```
* **If it DOES NOT exist or you get an error:** You need to compile the entire project. Run the following commands:
  ```bash
  cd ~/agri_scout_ws
  colcon build --symlink-install
  source install/setup.bash
  ```

### 3. Installing Python test dependencies
The test scripts you will run depend on some Python libraries, specifically the `psutil` tool to read CPU and Memory data from the Raspberry Pi.
Install it using the system package manager (recommended for Ubuntu 24.04+):
```bash
sudo apt update
sudo apt install python3-psutil
```

---

## Step 2: Starting Hardware Drivers (The Foundation)

⚠️ **VERY IMPORTANT:** The interactive test scripts (Step 3) **WILL NOT WORK** if the sensors are not logically connected. ROS 2 needs to be "awake" and translating the electrical signal from each USB cable into messages our scripts understand.

To stay organized, open **new terminal tabs** (using the terminal icon or screen/tmux) for each of the drivers below.

In **every new terminal/tab**, you **MUST** always run these two commands first:
```bash
source /opt/ros/jazzy/setup.bash
source ~/agri_scout_ws/install/setup.bash
```

### Terminal A (Arduino - Motors, Encoders, Ultrasound)
Ensure the Arduino is connected via USB and start the micro-ROS agent (if using micro-ROS) or rosserial. Usually, the port is `ttyUSB0`.
```bash
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0
# Tip: If it fails saying the port does not exist, disconnect and reconnect the Arduino 
# and run 'dmesg | grep tty' to see the correct name (e.g., ttyACM0).
```

### Terminal B (LiDAR - Laser Scanning Sensor)
Initialize the official LiDAR package. Adjust the launch file name (.py) if using a different model.
```bash
ros2 launch rplidar_ros rplidar_a2m12_launch.py
```

### Terminal C (RealSense Camera - Computer Vision)
Initialize the package that translates the USB image into a ROS image.
```bash
ros2 launch realsense2_camera rs_launch.py
```

**🤔 How to be sure it worked?**
Open any terminal, source the setup (`source /opt/ros/jazzy/setup.bash`) and run:
```bash
ros2 topic list
```
You should see a large list of words like `/scan`, `/odom`, `/camera/color/image_raw`. If they appear, congratulations! The sensors are communicating properly.

---

## Step 3: Running the Practical Hardware Tests

Finally, with the base system publishing data into the robot's veins, let's run the test scripts.
Return to the root of this README:
```bash
cd ~/AGRI-Scout/hardware_tests/
```

Give execution permissions to all scripts (only needs to be done once):
```bash
chmod +x *.py
```

And run them one by one in the suggested order:

### 1. System Monitor (Operation Heart)
```bash
./system_monitor.py
```
* **🔍 What to verify:** CPU usage is acceptable (under 80%), Temperature is not exceeding 75-80°C (preventing chip damage), and RAM is not maxed out (100% usage).

### 2. LiDAR and Camera (High-Throughput Sensors)
These sensors push the most data through the USB cable.
```bash
./test_lidar.py
./test_camera.py
```
* **🔍 What to verify:** Is the publishing frequency (Hz) fast and consistent? Does the LiDAR have points in the scan cloud? Does the Camera open and return at least the frame format (e.g., 640x480)?

### 3. IMU and GPS (Spatial Positioning Sensors)
```bash
./test_imu_gps.py
```
* **🔍 What to verify:** The X, Y, Z orientation from the IMU doesn't spin wildly when the robot is perfectly still on the ground. The GPS gets a satellite signal (valid Fix Status) outdoors.

### 4. Ultrasonic Sensors (Front and Side Bumpers)
```bash
./test_ultrasound.py
```
* **🔍 What to verify:** Place your hand in front of each sensor and observe in the terminal if the displayed distance drops correctly and tracks the real distance of your hand.

### 5. Motors (Odometry and Actuation) ✨ HIGH RISK ✨
⚠️ **RECOMMENDED:** Lift the robot's wheels and place it on a firm stool/block for your first attempt to prevent the robot from shooting forward and hitting someone.
```bash
./test_motors.py
```
* **🔍 What to verify:** 
  1. When pressing `W`, do both tracks/wheels move forward?
  2. Does the odometry value increase consistently?
  3. Press `A` (turn left) and `D` (turn right) - does it turn the correct way?
  4. Press and hold `SPACE` to ensure the instant brake works.

---
**🛠️ Pro Tip / General Troubleshooting:**
If you start any test from **Step 3** and see something like *"Waiting for data..."* permanently in the terminal (for over 10 seconds) and nothing else happens: **Your driver crashed.**
This means Step 2 failed somehow. Return to that driver's terminal, press `Ctrl+C` to kill the process, check the USB cable connections, and start it again.
