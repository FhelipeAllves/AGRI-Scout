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

# Speed intensity for new robust commands
MOVE_SPEED = 20

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
                send_command(f"F{MOVE_SPEED}")
                
            elif key == 'S':
                print("\r[MOVE] Backward               ", end='')
                send_command(f"B{MOVE_SPEED}")
                
            elif key == 'A':
                # Skid-steer handled by Arduino now
                print("\r[MOVE] Left                   ", end='')
                send_command(f"L{MOVE_SPEED}")
                
            elif key == 'D':
                # Skid-steer handled by Arduino now
                print("\r[MOVE] Right                  ", end='')
                send_command(f"R{MOVE_SPEED}")
                
            elif key == ' ' or key == 'P':
                print("\r[STOP] Stopping Wheels        ", end='')
                send_command("X")
                
            elif key == 'I':
                print("\r[PROBE] Moving DOWN continuously...   ", end='')
                send_command("D")
                
            elif key == 'K':
                print("\r[PROBE] Moving UP continuously...     ", end='')
                send_command("U")
                
            elif key == 'Q':
                print("\nExiting and stopping robot...")
                send_command("X")
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
        send_command("X") # Failsafe stop
        robot.close()
        print("Serial connection closed.")

if __name__ == "__main__":
    main()
