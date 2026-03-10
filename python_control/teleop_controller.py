import serial
import time
import sys
import termios
import tty
import select

# ==========================================
# CONFIGURATION
# ==========================================
SERIAL_PORT = '/dev/ttyACM0' # Ensure this matches your Pi's port
BAUD_RATE = 9600

# Speeds for the ESCs (90 is neutral)
SPEED_FWD = 110
SPEED_REV = 70
SPEED_NEUTRAL = 90

# Steps for the NEMA 17 Probe
PROBE_STEPS_AMOUNT = 200

# ==========================================
# SETUP SERIAL CONNECTION
# ==========================================
try:
    print(f"Connecting to Arduino on {SERIAL_PORT}...")
    robot = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) # Wait for Arduino to reset
    print("Connection established! Robot is ready.")
except serial.SerialException:
    print(f"ERROR: Could not connect to {SERIAL_PORT}.")
    sys.exit(1)

# ==========================================
# KEYBOARD INPUT HELPER (NON-BLOCKING)
# ==========================================
def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key.upper()

# ==========================================
# COMMAND FUNCTIONS
# ==========================================
def send_command(cmd):
    # Add newline so Arduino's parseInt() processes it immediately
    robot.write((cmd + '\n').encode('utf-8'))

# ==========================================
# MAIN TELEOPERATION LOOP
# ==========================================
def main():
    print("\n=== AGRI-SCOUT TELEOPERATION ===")
    print("W : Forward       I : Probe Down")
    print("S : Backward      K : Probe Up")
    print("A : Turn Left")
    print("D : Turn Right")
    print("SPACE : Stop All  Q : Quit")
    print("================================\n")

    try:
        while True:
            key = get_key()
            
            if key == 'W':
                print("\r[MOVE] Forward                ", end='')
                send_command(f"W{SPEED_FWD} {SPEED_FWD}")
                
            elif key == 'S':
                print("\r[MOVE] Backward               ", end='')
                send_command(f"W{SPEED_REV} {SPEED_REV}")
                
            elif key == 'A':
                # Skid-steer: Left reverse, Right forward
                print("\r[MOVE] Left                   ", end='')
                send_command(f"W{SPEED_REV} {SPEED_FWD}")
                
            elif key == 'D':
                # Skid-steer: Left forward, Right reverse
                print("\r[MOVE] Right                  ", end='')
                send_command(f"W{SPEED_FWD} {SPEED_REV}")
                
            elif key == ' ' or key == 'P':
                print("\r[STOP] Stopping Wheels        ", end='')
                send_command(f"W{SPEED_NEUTRAL} {SPEED_NEUTRAL}")
                
            elif key == 'I':
                print(f"\r[PROBE] Going DOWN ({PROBE_STEPS_AMOUNT} steps)", end='')
                send_command(f"S{PROBE_STEPS_AMOUNT}")
                
            elif key == 'K':
                print(f"\r[PROBE] Going UP ({-PROBE_STEPS_AMOUNT} steps)", end='')
                send_command(f"S{-PROBE_STEPS_AMOUNT}")
                
            elif key == 'Q':
                print("\nExiting and stopping robot...")
                send_command(f"W{SPEED_NEUTRAL} {SPEED_NEUTRAL}")
                break

            # Read feedback from Arduino to keep the buffer clean
            while robot.in_waiting > 0:
                try:
                    line = robot.readline().decode('utf-8').strip()
                    if line:
                        print(f"\n[Arduino]: {line}")
                except UnicodeDecodeError:
                    pass
            
            time.sleep(0.05) # Prevent CPU flooding

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        send_command(f"W{SPEED_NEUTRAL} {SPEED_NEUTRAL}") # Failsafe stop
        robot.close()
        print("Serial connection closed.")

if __name__ == "__main__":
    main()