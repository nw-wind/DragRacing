#!/usr/bin/env python3 

import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM) 
GPIO.setup(20, GPIO.OUT)
GPIO.setup(21, GPIO.OUT)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

led=0
def test_callback_23(channel):
    global led
    print(f'Event {led} detected for {channel}')
    led+=1
    GPIO.output(20,led%2)

def test_callback_24(channel):
    global led
    print(f'Event {led} detected for {channel}')
    led+=1
    GPIO.output(21,led%2)

GPIO.add_event_detect(23, GPIO.FALLING, callback=test_callback_23, bouncetime=250)
GPIO.add_event_detect(24, GPIO.RISING, callback=test_callback_24, bouncetime=250)


i=0
try:
    while (True):
        #GPIO.output(20,i%2)
        print(f"{i}")
        i+=1
        sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()

GPIO.cleanup()
