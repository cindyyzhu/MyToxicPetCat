from gpiozero import Motor, PWMOutputDevice
from time import sleep

# IN1, IN2
motor1 = Motor(forward=16, backward=20)
motor1_enable = PWMOutputDevice(21)  # EN1 pin

motor2 = Motor(forward=19, backward=26)
motor2_enable = PWMOutputDevice(13)  # EN2 pin

# Enable motors
motor1_enable.on()
motor2_enable.on()

print("Running the motors...")

while True:
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
