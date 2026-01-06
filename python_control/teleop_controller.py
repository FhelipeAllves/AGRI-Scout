import serial
import time
import sys
import termios
import tty
import select

# --- CONFIGURATION ---
SERIAL_PORT = '/dev/ttyACM0' # Check if it is ACM0 or USB0
BAUD_RATE = 9600

# --- SETUP SERIAL CONNECTION ---
try:
    print(f"Connecting to Arduino on {SERIAL_PORT}...")
    robot = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) # Wait for Arduino to reset/reboot
    print("Connection established! Robot is ready.")
except serial.SerialException:
    print(f"ERROR: Could not connect to {SERIAL_PORT}.")
    sys.exit(1)

# --- KEYBOARD INPUT HELPER ---
# This function reads a single keypress without requiring 'Enter'
def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        # Check if there is input available (non-blocking check)
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key.upper()

# --- MAIN LOOP ---
def main():
    print("\n--- AGRI-SCOUT TELEOPERATION ---")
    print("CONTROLS: [W] Forward  [S] Backward  [A] Left  [D] Right")
    print("          [SPACE] Stop  [T] Telemetry (Sensors)  [Q] Quit")
    print("---------------------------------------------------------")

    try:
        while True:
            # 1. Get User Input
            key = get_key()
            
            command_sent = False
            
            if key == 'W':
                robot.write(b'F')
                command_sent = True
            elif key == 'S':
                robot.write(b'B') # Backward
                command_sent = True
            elif key == 'A':
                robot.write(b'L')
                command_sent = True
            elif key == 'D':
                robot.write(b'R')
                command_sent = True
            elif key == ' ' or key == 'P':
                robot.write(b'S') # Stop
                print("\r[STOP] Stopping Motors...", end='')
                command_sent = True
            elif key == 'T':
                robot.write(b'T') # Telemetry
                print("\r[DATA] Requesting Sensor Data...", end='')
                command_sent = True
            elif key == 'Q':
                print("\nExiting...")
                robot.write(b'S') # Stop before quitting
                break

            # 2. Read Feedback from Arduino (The "Reflex")
            # The Arduino sends back text like "MOVING_FWD" or "WARNING: OBSTACLE"
            if robot.in_waiting > 0:
                try:
                    line = robot.readline().decode('utf-8').strip()
                    if line:
                        # Clear line and print status
                        print(f"\rRobot Status: {line}              ", end='')
                except:
                    pass
            
            # Small delay to prevent CPU flooding
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        robot.close()
        print("Serial connection closed.")

if __name__ == "__main__":
    main()