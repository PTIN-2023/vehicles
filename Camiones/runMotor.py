#!/usr/bin/env python

import RPi.GPIO as GPIO
from time import sleep

# Right Motor
IN1 = 11
IN2 = 13
IN3 = 29
IN4 = 31

GPIO.setmode(GPIO.BOARD)

GPIO.setup(IN1,GPIO.OUT)
GPIO.setup(IN2,GPIO.OUT)
GPIO.setup(IN3,GPIO.OUT)
GPIO.setup(IN4,GPIO.OUT)

GPIO.output(IN1,GPIO.LOW)
GPIO.output(IN2,GPIO.LOW)
GPIO.output(IN3,GPIO.LOW)
GPIO.output(IN4,GPIO.LOW)

try:
    # Create Infinite loop to read user input
    while True:
        # Get user Input
        user_input = input()

        # To see users input
        # print(user_input)

        if user_input == 'f':
            GPIO.output(IN1,GPIO.HIGH)
            GPIO.output(IN2,GPIO.LOW)

            GPIO.output(IN3,GPIO.HIGH)
            GPIO.output(IN4,GPIO.LOW)

            print("Forward")
        
        elif user_input == 'b':
            GPIO.output(IN1,GPIO.LOW)
            GPIO.output(IN2,GPIO.HIGH)

            GPIO.output(IN3,GPIO.LOW)
            GPIO.output(IN4,GPIO.HIGH)

            print("Backwards")

        elif user_input == 'l':
            GPIO.output(IN1,GPIO.HIGH)
            GPIO.output(IN2,GPIO.LOW)

            GPIO.output(IN3,GPIO.LOW)
            GPIO.output(IN4,GPIO.LOW)

        elif user_input == 'r':
            GPIO.output(IN1,GPIO.LOW)
            GPIO.output(IN2,GPIO.LOW)

            GPIO.output(IN3,GPIO.HIGH)
            GPIO.output(IN4,GPIO.LOW)
        
        elif user_input == 's':
            GPIO.output(IN1,GPIO.LOW)
            GPIO.output(IN2,GPIO.LOW)

            GPIO.output(IN3,GPIO.LOW)
            GPIO.output(IN4,GPIO.LOW)

            print("Stop")


except KeyboardInterrupt:
    # Reset GPIO settings
    GPIO.cleanup()
    print("GPIO Clean up")