import serial

# Find your Arduino serial port. Usually /dev/ttyACM0 or /dev/ttyUSB0
arduino = serial.Serial('/dev/ttyACM0', 9600)

while True:
    data = arduino.readline().decode().strip()
    if data:
        print(f"Mic value: {data}")
