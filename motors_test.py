import RPi.GPIO as GPIO
import time

# -----------------------------
# Motor 1 pins
IN1 = 17
IN2 = 27
EN1 = 18

# Motor 2 pins
IN3 = 22
IN4 = 23
EN2 = 19
# -----------------------------

GPIO.setmode(GPIO.BCM)

# Set up all pins
for pin in [IN1, IN2, IN3, IN4, EN1, EN2]:
    GPIO.setup(pin, GPIO.OUT)

# Set up PWM on enable pins (for speed control)
pwm1 = GPIO.PWM(EN1, 1000)  # 1 kHz
pwm2 = GPIO.PWM(EN2, 1000)  # 1 kHz

# Start PWM at full speed
pwm1.start(100)  # 0-100%
pwm2.start(100)

try:
    while True:
        # Motor 1 forward
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        
        # Motor 2 forward
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        
        print("Motors spinning forward")
        time.sleep(2)

        # Motor 1 backward
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        
        # Motor 2 backward
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        
        print("Motors spinning backward")
        time.sleep(2)

        # Stop motors
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.LOW)
        
        print("Motors stopped")
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    pwm1.stop()
    pwm2.stop()
    GPIO.cleanup()
