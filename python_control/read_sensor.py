import minimalmodbus
import serial
import time
import csv
import sys
from datetime import datetime

# Configuration constants
SERIAL_PORT = '/dev/ttyUSB1'
SLAVE_ADDRESS = 1
BAUD_RATE = 9600
OUTPUT_FILE = 'sensor_data_log_corrigido.csv'

def read_and_log_sensor_data():
    """
    Connects to the 8-parameter sensor, updates the terminal in place,
    and saves the session data to a CSV file upon exit (Ctrl+C).
    """
    try:
        instrument = minimalmodbus.Instrument(SERIAL_PORT, SLAVE_ADDRESS)
        instrument.serial.baudrate = BAUD_RATE
        instrument.serial.bytesize = 8
        instrument.serial.parity = serial.PARITY_NONE
        instrument.serial.stopbits = 1
        instrument.serial.timeout = 1.0
        instrument.mode = minimalmodbus.MODE_RTU
    except Exception as connection_error:
        print(f"Failed to initialize port: {connection_error}")
        return

    session_data = []
    
    sys.stdout.write('\033[2J\033[H')
    sys.stdout.flush()

    try:
        while True:
            try:
                # CRITICAL FIX: Reading 8 registers instead of 7
                sensor_data = instrument.read_registers(registeraddress=0, number_of_registers=8, functioncode=3)
                
                # Correct physical mapping based on data analysis
                temperature = sensor_data[0] / 10.0
                humidity = sensor_data[1] / 10.0
                electrical_conductivity = sensor_data[2]
                salinity = sensor_data[3]          # Was previously mislabeled as pH
                nitrogen = sensor_data[4]
                phosphorus = sensor_data[5]
                potassium = sensor_data[6]
                ph_value = sensor_data[7] / 10.0   # The actual pH register!

                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                session_data.append([
                    current_time, temperature, humidity, electrical_conductivity, 
                    salinity, nitrogen, phosphorus, potassium, ph_value
                ])

                sys.stdout.write('\033[H')
                print("=== Live Sensor Reading (8 Parameters) ===")
                print(f"Timestamp:     {current_time}")
                print(f"Temperature:   {temperature:.1f} °C")
                print(f"Humidity:      {humidity:.1f} %")
                print(f"Conductivity:  {electrical_conductivity} us/cm")
                print(f"Salinity:      {salinity} mg/L")
                print(f"Nitrogen (N):  {nitrogen} mg/kg")
                print(f"Phosphorus (P):{phosphorus} mg/kg")
                print(f"Potassium (K): {potassium} mg/kg")
                print(f"pH Level:      {ph_value:.1f}")
                print("-" * 42)
                print("Press Ctrl+C to stop and save data...")
                
                sys.stdout.write('\033[J') 
                sys.stdout.flush()
                
            except Exception as read_error:
                sys.stdout.write('\033[H')
                print(f"Error reading from sensor: {read_error}")
                print("Retrying in 1 second...          ")
                sys.stdout.write('\033[J')
                sys.stdout.flush()
            
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nExecution stopped by user. Generating CSV file...")
        save_to_csv(session_data)


def save_to_csv(data_buffer):
    """
    Saves the properly mapped sensor data matrix to a CSV file.
    """
    if not data_buffer:
        return

    headers = [
        'Timestamp', 'Temperature_C', 'Humidity_Percent', 'Conductivity_us_cm', 
        'Salinity_mg_L', 'Nitrogen_mg_kg', 'Phosphorus_mg_kg', 'Potassium_mg_kg', 'pH'
    ]

    try:
        with open(OUTPUT_FILE, mode='w', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(headers)
            csv_writer.writerows(data_buffer)
        print(f"Success! Session data saved to: {OUTPUT_FILE}")
    except Exception as file_error:
        print(f"Failed to write CSV file: {file_error}")


if __name__ == '__main__':
    read_and_log_sensor_data()
