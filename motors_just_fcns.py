import RPi.GPIO as GPIO
import time

# ==========================================
# SETUP (This runs once when imported)
# ==========================================
MotorA_in1 = 17
MotorA_in2 = 27
MotorB_in3 = 22
MotorB_in4 = 23
MotorA_en = 18
MotorB_en = 24

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False) # Prevents annoying warnings if you restart the script quickly

GPIO.setup([MotorA_in1, MotorA_in2, MotorB_in3, MotorB_in4], GPIO.OUT)
GPIO.setup([MotorA_en, MotorB_en], GPIO.OUT)

# PWM setup for speed control
pwmA = GPIO.PWM(MotorA_en, 100)  # 100Hz
pwmB = GPIO.PWM(MotorB_en, 100)
pwmA.start(0)
pwmB.start(0)

# ==========================================
# FUNCTIONS (Available to your main script)
# ==========================================
def motorA_forward(speed=50):
    GPIO.output(MotorA_in1, GPIO.HIGH)
    GPIO.output(MotorA_in2, GPIO.LOW)
    pwmA.ChangeDutyCycle(speed)

def motorB_forward(speed=50):
    GPIO.output(MotorB_in3, GPIO.HIGH)
    GPIO.output(MotorB_in4, GPIO.LOW)
    pwmB.ChangeDutyCycle(speed)

def stop_motors():
    GPIO.output([MotorA_in1, MotorA_in2, MotorB_in3, MotorB_in4], GPIO.LOW)
    pwmA.ChangeDutyCycle(0)
    pwmB.ChangeDutyCycle(0)

def cleanup_motors():
    """Wipes the GPIO pins. Call this when your main program shuts down."""
    stop_motors()
    pwmA.stop()
    pwmB.stop()
    GPIO.cleanup()

# ==========================================
# TEST BLOCK (Ignored during import)
# ==========================================
if __name__ == "__main__":
    try:
        print("Testing: Motors forward for 3 seconds")
        motorA_forward(80)
        motorB_forward(80)
        time.sleep(3)

        print("Stopping motors")
        stop_motors()

    finally:
        cleanup_motors()
        print("GPIO Cleaned up. Test complete.")