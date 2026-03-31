#!/usr/bin/env python3
import serial
import time

# ==========================================
# RAW SERIAL COMMUNICATION TEST
# ==========================================

def main():
    try:
        # Initialize direct serial connection to Arduino
        arduino = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
        print("Connecting to Arduino... Please wait 2 seconds.")
        time.sleep(2) # Give Arduino time to reboot after serial connection
        
        print("\n--- DIRECT HARDWARE TEST ---")
        print("Available Commands:")
        print("  W<left_speed> <right_speed>  -> Example: W110 110 (Move wheels)")
        print("  W90 90                       -> Stop wheels")
        print("  S<steps>                     -> Example: S200 (Move probe)")
        print("Type 'exit' to quit.\n")

        while True:
            user_input = input("Enter command: ")
            
            if user_input.lower() == 'exit':
                print("Closing connection.")
                break
                
            # The Arduino code expects a newline character '\n' at the end
            command_to_send = f"{user_input}\n"
            arduino.write(command_to_send.encode('utf-8'))
            
            # Read back the Acknowledgment from Arduino
            time.sleep(0.1)
            while arduino.in_waiting > 0:
                response = arduino.readline().decode('utf-8').strip()
                print(f"[ARDUINO REPLIES]: {response}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'arduino' in locals() and arduino.is_open:
            arduino.close()

if __name__ == '__main__':
    main()

