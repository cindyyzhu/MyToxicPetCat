# Raspberry Pi: control motors using L293D
from gpiozero import Motor, OutputDevice
from time import sleep


# Make pins to output signals
motor1 = Motor(16, 20, enable=21)
motor2 = Motor(19, 26, enable=13)

print("Running the motors...")

while True:
    # Rotate motors in different directions:
    motor1.forward()
    motor2.forward()
    sleep(3)
    motor1.stop()
    motor2.stop()
    sleep(0.1)
    motor1.backward()
    motor2.backward()
    sleep(3)
    motor1.stop()
    motor2.stop()
    sleep(3)
    