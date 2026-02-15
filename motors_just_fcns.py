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

# Servo Stuff
LEFT_EAR_CHANNEL = 0
RIGHT_EAR_CHANNEL = 1

#GPIO.setup(LEFT_EAR_PIN, GPIO.OUT)
#GPIO.setup(RIGHT_EAR_PIN, GPIO.OUT)

#left_ear = GPIO.PWM(LEFT_EAR_PIN, 50)
#right_ear = GPIO.PWM(RIGHT_EAR_PIN, 50)

#left_ear.start(0)
#right_ear.start(0)

#left_current_angle = 90
#right_current_angle = 90

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

"""
# SERVO functions
def angle_to_duty_cycle(angle):
    
    Convert angle (0-180) to duty cycle (2-12)
    Most servos: 2% = 0°, 7% = 90°, 12% = 180°
    Adjust these values if your servos behave differently
    
    return 2 + (angle / 180) * 10


def set_servo_angle(pwm, angle):
    Set servo to specific angle
    duty = angle_to_duty_cycle(angle)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.01)  # Small delay for servo to respond
    pwm.ChangeDutyCycle(0)  # Stop sending signal to prevent jitter


def sweep_to_angle(pwm, target_angle, current_angle, speed=0.05):
    
    Smoothly sweep servo from current position to target angle.
    
    Args:
        pwm: The PWM object to control
        target_angle: Target angle in degrees (0-180)
        current_angle: Current angle in degrees (0-180)
        speed: Delay between steps in seconds (lower = faster)
    
    Returns:
        float: The final angle position
    
    # Clamp target angle to valid range
    target_angle = max(0, min(180, target_angle))
    
    # Determine direction and step size
    if target_angle > current_angle:
        step = 1
    elif target_angle < current_angle:
        step = -1
    else:
        return current_angle  # Already at target
    
    # Sweep from current to target
    for angle in range(int(current_angle), int(target_angle) + step, step):
        set_servo_angle(pwm, angle)
        time.sleep(speed)
    
    # Ensure we end exactly at target
    set_servo_angle(pwm, target_angle)
    
    return target_angle


def sweep_left_ear(target_angle, speed=0.05):
 Sweep left ear to target angle
    global left_current_angle
    left_current_angle = sweep_to_angle(left_ear, target_angle, left_current_angle, speed)


def sweep_right_ear(target_angle, speed=0.05):
    #Sweep right ear to target angle
    global right_current_angle
    right_current_angle = sweep_to_angle(right_ear, target_angle, right_current_angle, speed)


def sweep_both_ears(target_angle, speed=0.05):
    Sweep both ears to the same target angle
    sweep_left_ear(target_angle, speed)
    sweep_right_ear(target_angle, speed)


def reset_ears():
    Reset both ears to center position (90 degrees)
    sweep_both_ears(90)


def cleanup():
    Clean up GPIO on exit
    left_ear.stop()
    right_ear.stop()
    GPIO.cleanup()

#set_servo_angle(left_ear, left_current_angle)
#set_servo_angle(right_ear, right_current_angle)

"""
# ==========================================
# TEST BLOCK (Ignored during import)
# ==========================================
if __name__ == "__main__":
    # Initialize servos to center position
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
