#!/usr/bin/env python3

import serial
import time
import sys
import termios
import tty
import select

# ==========================================
# CONFIGURATION
# ==========================================
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
MOVE_SPEED = 30 # A intensity offset (e.g., 90 - 30 = 60 PWM)

# Protocol Markers
START_BYTE = 0x3C # '<'
END_BYTE = 0x3E   # '>'

try:
    print(f"Connecting to Arduino on {SERIAL_PORT}...")
    robot = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    time.sleep(2)
    print("✅ Connection established! Robot is ready.")
except serial.SerialException:
    print(f"❌ ERROR: Could not connect to {SERIAL_PORT}.")
    sys.exit(1)

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key.upper()

def send_secure_command(cmd_char, value=0):
    cmd_byte = ord(cmd_char)
    # Checksum calculation: XOR the command and the value
    checksum = cmd_byte ^ value
    
    packet = bytearray([START_BYTE, cmd_byte, value, checksum, END_BYTE])
    robot.write(packet)
    robot.flush()

def main():
    print("\n=== AGRI-SCOUT SECURE TELEOP ===")
    print("W : Forward       I : Probe UP")
    print("S : Backward      K : Probe DOWN")
    print("A : Turn Left")
    print("D : Turn Right")
    print("SPACE : Stop All  Q : Quit")
    print("================================\n")

    current_action = ('X', 0)
    current_label = "[STOP] Idle"
    last_action = ('', 0)
    last_action_time = 0

    try:
        while True:
            key = get_key()
            
            if key == 'W':
                current_label = "[MOVE] Forward"
                current_action = ('F', MOVE_SPEED)
            elif key == 'S':
                current_label = "[MOVE] Backward"
                current_action = ('B', MOVE_SPEED)
            elif key == 'A':
                current_label = "[MOVE] Left"
                current_action = ('L', MOVE_SPEED)
            elif key == 'D':
                current_label = "[MOVE] Right"
                current_action = ('R', MOVE_SPEED)
            elif key == 'I':
                current_label = "[PROBE] Moving UP"
                current_action = ('U', 0)
            elif key == 'K':
                current_label = "[PROBE] Moving DOWN"
                current_action = ('D', 0)
            elif key == ' ' or key == 'P':
                current_label = "[STOP] Halting"
                current_action = ('X', 0)
            elif key == 'Q':
                print("\nExiting...")
                send_secure_command('X', 0)
                break

            # Send command if changed
            if current_action != last_action:
                print(f"\x1b[2K\r> {current_label}", end='', flush=True)
                send_secure_command(*current_action)
                last_action = current_action
                last_action_time = time.time()
            # Watchdog feeder (Sends the command again before 1 second expires)
            elif time.time() - last_action_time > 0.4:
                send_secure_command(*current_action)
                last_action_time = time.time()

            # Print feedback from Arduino safely
            while robot.in_waiting > 0:
                try:
                    line = robot.readline().decode('utf-8').strip()
                    if line:
                        print(f"\n[Arduino]: {line}")
                        print(f"\x1b[2K\r> {current_label}", end='', flush=True)
                except UnicodeDecodeError:
                    pass

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        send_secure_command('X', 0)
        robot.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()