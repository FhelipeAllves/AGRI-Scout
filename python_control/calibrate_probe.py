import serial
import time
import sys

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600

def main():
    print("========================================")
    print(" PROBE PRECISION CALIBRATOR (MECHANICAL LIMITS)")
    print("========================================")
    print("WARNING: To avoid structural damage, the vehicle must")
    print("be suspended or on clear terrain free of large rocks.\n")
    
    try:
        robot = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)  # Wait for Arduino reset
        print("[SUCCESS] Connected to Arduino.")
    except Exception as e:
        print(f"[ERROR] Unable to connect to port {SERIAL_PORT}: {e}")
        sys.exit(1)

    # Clear initial buffer
    robot.reset_input_buffer()

    posicao_maxima_sonda = 0

    print("\nINSTRUCTIONS:")
    print("- Enter a POSITIVE number (e.g. 50) to lower the probe.")
    print("- Enter a NEGATIVE number (e.g. -50) to raise the probe.")
    print("- Use small values (like 10 or 20) when getting close to the base.")
    print("- Enter '0' or press Ctrl+C to exit.\n")
    print(f"--> Current Rail Position: {posicao_maxima_sonda} Steps.")

    try:
        while True:
            comando = input("\n[ENTER STEPS]: ").strip()
            
            if not comando:
                continue

            try:
                passos = int(comando)
            except ValueError:
                print("Please enter only valid numbers.")
                continue

            if passos == 0:
                print("Exiting calibrator...")
                break

            # Send S command (Step Control)
            msg = f"S{passos}\n"
            robot.write(msg.encode('utf-8'))
            
            print("Waiting for motor...")
            
            # Read Arduino feedback until Complete
            while True:
                linha = robot.readline().decode('utf-8').strip()
                if linha:
                    print(f" > {linha}")
                    if "Probe movement complete" in linha:
                        break
            
            # Update blind count based on commanded steps (Open-Loop Step Tracking)
            posicao_maxima_sonda += passos
            
            print("="*40)
            print(f"🧭 RELATIVE DISTANCE COUNTED SO FAR: {posicao_maxima_sonda} Steps")
            print("="*40)
            print("Note down this Position number if the probe just hit the bottom!")

    except KeyboardInterrupt:
        print("\n[Emergency Stop] Calibrator terminated by user.")
    finally:
        robot.close()
        print(f"\n--- FINAL CALIBRATION ---\nThe total depth or maximum stroke measured was: {posicao_maxima_sonda}. Note this down!")

if __name__ == '__main__':
    main()
