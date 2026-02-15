import RPi.GPIO as GPIO
import time

MotorA_in1 = 17
MotorA_in2 = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup([MotorA_in1, MotorA_in2], GPIO.OUT)

try:
    GPIO.output(MotorA_in1, GPIO.HIGH)
    GPIO.output(MotorA_in2, GPIO.LOW)
    time.sleep(3)
finally:
    GPIO.output([MotorA_in1, MotorA_in2], GPIO.LOW)
    GPIO.cleanup()
