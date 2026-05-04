import serial
import time

# --- CONFIGURATION ---
usb_port = '/dev/ttyACM0'  # Confirm using 'ls /dev/tty*'
baud_rate = 9600

print(f"Trying to connect to Arduino on {usb_port}...")

try:
    # 1. Open the serial connection
    arduino = serial.Serial(usb_port, baud_rate, timeout=1)
    
    print("Waiting for Arduino to reset (2 seconds)...")
    time.sleep(2)
    print("Connection established! Starting test loop.\n")

    # 2. Command sending loop
    while True:
        # Ask the user what to do
        command = input("Type 'L' to turn ON, 'D' to turn OFF, or 'S' to Exit: ").upper()

        if command == 'S':
            print("Closing connection.")
            arduino.close()
            break

        # Send only valid commands
        if command in ['L', 'D']:
            # 3. SEND COMMAND (encode converts text to bytes)
            arduino.write(command.encode('utf-8'))
            
            # 4. READ RESPONSE (waits for Arduino reply)
            # readline() blocks until a newline character (\n) is received
            response = arduino.readline().decode('utf-8').strip()
            
            if response:
                print(f"Received response: {response}")
            else:
                print("No response from Arduino (Timeout).")
        else:
            print("Invalid command. Please try again.")

except serial.SerialException:
    print("CRITICAL ERROR: Unable to find the Arduino.")
    print("Tip: Check if the cable is connected and the port is /dev/ttyACM0")
except KeyboardInterrupt:
    print("\nProgram interrupted by user.")
