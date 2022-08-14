#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import threading

pinA = 23
pinB = 24
pinC = 27
pinD = 22

freq = 7500  # cycle frequency
period = 1.0/freq


Done = False
power_left  = 0.0
power_right = 0.0

GPIO.setmode( GPIO.BCM )
GPIO.setup( pinA, GPIO.OUT )
GPIO.setup( pinB, GPIO.OUT )
GPIO.setup( pinC, GPIO.OUT )
GPIO.setup( pinD, GPIO.OUT )

GPIO.output(pinA, False)
GPIO.output(pinB, False)
GPIO.output(pinC, False)
GPIO.output(pinD, False)


def PWM_left_update_thread():
	while not Done:

		if power_left>0.0:
			pinL_gnd = pinB
			pinL_pwm = pinA
		else:
			pinL_gnd = pinA
			pinL_pwm = pinB
		dutyL = abs(power_left)

		GPIO.output(pinL_gnd, False)
		GPIO.output(pinL_pwm, True)
		time.sleep( period*dutyL );
		GPIO.output(pinL_pwm, False)
		time.sleep( period*(1.0-dutyL) );

def PWM_right_update_thread():
	while not Done:

		if power_right>0.0:
			pinR_gnd = pinD
			pinR_pwm = pinC
		else:
			pinR_gnd = pinC
			pinR_pwm = pinD
		dutyR = abs(power_right)

		GPIO.output(pinR_gnd, False)
		GPIO.output(pinR_pwm, True)
		time.sleep( period*dutyR );
		GPIO.output(pinR_pwm, False)
		time.sleep( period*(1.0-dutyR) );



def move( powerL, powerR, t ):
	global power_left, power_right
	power_left  = powerL
	power_right = powerR
	time.sleep( t )
	power_left  = 0.0
	power_right = 0.0


pwm_left_thread  = threading.Thread( target=PWM_left_update_thread  )
pwm_right_thread = threading.Thread( target=PWM_right_update_thread )
pwm_left_thread.start()
pwm_right_thread.start()

move( 1.0, 1.0, 3 )
move( -1.0, -1.0, 3 )

Done = True
pwm_left_thread.join()
pwm_right_thread.join()
GPIO.cleanup()
