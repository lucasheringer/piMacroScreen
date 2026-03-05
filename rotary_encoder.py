#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
from usbHidKeyboard import send

RoAPin = 20    # CLK Pin
RoBPin = 21    # DT Pin
BtnPin = 16    # Button Pin

globalCounter = 0

flag = 0
Last_RoB_Status = 0
Current_RoB_Status = 0
buttonPressed = False

# Small sleeps keep polling responsive while avoiding a full CPU core spin.
INNER_POLL_SLEEP = 0.0005
MAIN_LOOP_SLEEP = 0.001

def trigger_action(action_value):
	try:
		send(action_value, '/dev/hidg0')
	except Exception as e:
		print(f"Failed to send {action_value}: {e}")

def setup():
	GPIO.setmode(GPIO.BCM)         # Numbers GPIOs by Broadcom SOC channel
	GPIO.setup(RoAPin, GPIO.IN)    # input mode
	GPIO.setup(RoBPin, GPIO.IN)
	GPIO.setup(BtnPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def rotaryDeal():
	global flag
	global Last_RoB_Status
	global Current_RoB_Status
	global globalCounter
	Last_RoB_Status = GPIO.input(RoBPin)
	while not GPIO.input(RoAPin):
		Current_RoB_Status = GPIO.input(RoBPin)
		flag = 1
		time.sleep(INNER_POLL_SLEEP)
	if flag == 1:
		flag = 0
		if (Last_RoB_Status == 0) and (Current_RoB_Status == 1):
			globalCounter = globalCounter + 1
		if (Last_RoB_Status == 1) and (Current_RoB_Status == 0):
			globalCounter = globalCounter - 1

def btnISR(channel):
	global buttonPressed
	buttonPressed = True

def loop():
	global buttonPressed
	tmp = 0	# Rotary Temperary

	button_interrupt_enabled = False
	try:
		GPIO.remove_event_detect(BtnPin)
	except RuntimeError:
		pass

	try:
		GPIO.add_event_detect(BtnPin, GPIO.FALLING, callback=btnISR, bouncetime=200)
		button_interrupt_enabled = True
	except RuntimeError as e:
		print(f"Warning: button edge detect unavailable ({e}). Using polling fallback.")

	while True:
		rotaryDeal()
		if not button_interrupt_enabled and GPIO.input(BtnPin) == GPIO.LOW:
			btnISR(BtnPin)
			time.sleep(0.2)
		if buttonPressed:
			trigger_action('MUTE')
			buttonPressed = False
		if tmp != globalCounter:
			if globalCounter > tmp:
				trigger_action('VOLUME_UP')
			else:
				trigger_action('VOLUME_DOWN')
			print(f'globalCounter = {globalCounter}')
			tmp = globalCounter
		time.sleep(MAIN_LOOP_SLEEP)

def destroy():
	GPIO.cleanup()             # Release resource

if __name__ == '__main__':     # Program start from here
	setup()
	try:
		loop()
	except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
		destroy()