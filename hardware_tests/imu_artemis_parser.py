import serial
import math

# Configure Raspberry Pi serial port (GPIO pins 14 and 15)
# 115200 baud rate is the OpenLog Artemis firmware default
porta_serial = '/dev/ttyS0'
baud_rate = 115200

try:
    ser = serial.Serial(porta_serial, baud_rate, timeout=1)
    print("Connected to Artemis! Reading data...")
except Exception as e:
    print(f"Error opening serial port: {e}")
    exit()

while True:
    try:
        # Read serial line and remove whitespace/newlines
        linha = ser.readline().decode('utf-8').strip()
        
        # Ignore empty lines
        if not linha:
            continue
            
        # Split line by commas
        dados = linha.split(',')
        
        # Ensure line has enough data before reading
        if len(dados) >= 5:
            # Extract Q1, Q2, and Q3 (indices 2, 3, and 4)
            q1 = float(dados[2])
            q2 = float(dados[3])
            q3 = float(dados[4])
            
            # --- START MATH (Translated from C++) ---
            
            # Calculate Q0: sqrt(1.0 - (q1^2 + q2^2 + q3^2))
            # "max(0.0, ...)" prevents negative root error due to float imprecision
            q0 = math.sqrt(max(0.0, 1.0 - ((q1 * q1) + (q2 * q2) + (q3 * q3))))
            
            q2sqr = q2 * q2

            # Roll (X-axis rotation)
            t0 = +2.0 * (q0 * q1 + q2 * q3)
            t1 = +1.0 - 2.0 * (q1 * q1 + q2sqr)
            roll = math.degrees(math.atan2(t0, t1))

            # Pitch (Y-axis rotation)
            t2 = +2.0 * (q0 * q2 - q3 * q1)
            t2 = max(-1.0, min(1.0, t2)) # Clamp between -1 and 1 (Gimbal lock prevention)
            pitch = math.degrees(math.asin(t2))

            # Yaw (Z-axis rotation)
            t3 = +2.0 * (q0 * q3 + q1 * q2)
            t4 = +1.0 - 2.0 * (q2sqr + q3 * q3)
            yaw = math.degrees(math.atan2(t3, t4))
            
            # --- END MATH ---

            # --- CALIBRATION / OFFSETS ---
            # Board is mounted upside down (Roll ~ 180) 
            # and True North reads as 81.6.
            
            def wrap_180(angle):
                """Wrap degree to -180° to +180° range"""
                while angle > 180.0: angle -= 360.0
                while angle <= -180.0: angle += 360.0
                return angle

            # Offset of -179.8 to align car roof "Flat" (0 degrees)
            roll_corrected = wrap_180(roll - 179.8)
            
            # Pitch does not need offset yet
            pitch_corrected = pitch 
            
            # Subtracting 81.6 forces "North" (was 81.6) to read exactly "0.0"
            yaw_corrected = wrap_180(yaw - 81.6)
            
            # Print results formatted to 1 decimal place
            print(f"Roll: {roll_corrected:6.1f}° | Pitch: {pitch_corrected:6.1f}° | Yaw (Compass): {yaw_corrected:6.1f}°")
            
    except ValueError:
        # Ignore boot garbage lines that cannot be cast to float
        pass
    except KeyboardInterrupt:
        print("\nReading terminated.")
        break
