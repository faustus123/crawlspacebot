#!/usr/bin/env python3
#
#  Run this on the robot (raspberry pi)
#

import os
import zmq
import time
import sys
import subprocess
import threading

# Reduces the jitter on the servos
os.environ["GPIOZERO_PIN_FACTORY"] = "pigpio"
os.system("sudo pigpiod")


import RPi.GPIO as GPIO
from gpiozero import Servo


port = "71400"  # For zmq commands
Done = False

# Camera angle servo control
pinH = 20
pinV = 21

# Laser control
pinLaser = 19

# Headlight control
pinHeadlight = 17

# Emergency pusher
pinEmergencyPusher = 22

servoH = Servo( pinH )
servoV = Servo( pinV )
servoH.mid()
servoV.mid()

# Emergency pusher is type UCTRONICS 270 degree servo.
# it has a min/max pulse width range of 0.5/2.5 ms
servoEmergencyPusher = Servo( pinEmergencyPusher, min_pulse_width=0.0005, max_pulse_width=0.0025, initial_value=-0.9 )

# tread DC motor control
pin_ENA = 18 # grey    <--|
pin_IN1 = 23 # white      |-- Left
pin_IN2 = 24 # black   <--|

pin_IN3 = 25 # brown   <--|
pin_IN4 = 12 # red        |-- Right
pin_ENB = 16 # orange  <--|


freq = 2000  # cycle frequency
period = 1.0/freq

power_left  = 0.0
power_right = 0.0
motors_stopped = True
headlight_power = 0.5
headlight_on = False

GPIO.setmode( GPIO.BCM )
GPIO.setup( pin_ENA, GPIO.OUT )
GPIO.setup( pin_IN1, GPIO.OUT )
GPIO.setup( pin_IN2, GPIO.OUT )
GPIO.setup( pin_IN3, GPIO.OUT )
GPIO.setup( pin_IN4, GPIO.OUT )
GPIO.setup( pin_ENB, GPIO.OUT )

GPIO.output(pin_ENA, False)
GPIO.output(pin_IN1, False)
GPIO.output(pin_IN2, False)
GPIO.output(pin_IN3, False)
GPIO.output(pin_IN4, False)
GPIO.output(pin_ENB, False)

GPIO.setup( pinLaser, GPIO.OUT )
GPIO.output(pinLaser, True)  # high is off

GPIO.setup( pinHeadlight, GPIO.OUT )
GPIO.output(pinHeadlight, False)  # start with headlight off


def PWM_left_update_thread():
	while not Done:
		if motors_stopped:
			GPIO.output(pin_IN1, False)
			GPIO.output(pin_IN2, False)
			GPIO.output(pin_ENA, False)
			time.sleep( period )
			continue

		if power_left>0.0:
			pinL_lo = pin_IN1
			pinL_hi = pin_IN2
		else:
			pinL_lo = pin_IN2
			pinL_hi = pin_IN1
		dutyL = abs(power_left)
		if dutyL > 1.0 : dutyL = 1.0

		GPIO.output(pinL_lo, False)
		GPIO.output(pinL_hi, True)
		GPIO.output(pin_ENA, True)
		time.sleep( period*dutyL );
		GPIO.output(pin_ENA, False)
		time.sleep( period*(1.0-dutyL) );

def PWM_right_update_thread():
	while not Done:
		if motors_stopped:
			GPIO.output(pin_IN3, False)
			GPIO.output(pin_IN4, False)
			GPIO.output(pin_ENB, False)
			time.sleep( period )
			continue

		if power_right>0.0:
			pinR_lo = pin_IN4
			pinR_hi = pin_IN3
		else:
			pinR_lo = pin_IN3
			pinR_hi = pin_IN4
		dutyR = abs(power_right)
		if dutyR > 1.0 : dutyR = 1.0

		GPIO.output(pinR_lo, False)
		GPIO.output(pinR_hi, True)
		GPIO.output(pin_ENB, True)
		time.sleep( period*dutyR );
		GPIO.output(pin_ENB, False)
		time.sleep( period*(1.0-dutyR) );

def PWM_headlight_update_thread():
	global headlight_power
	while not Done:
		if not headlight_on:
			GPIO.output(pinHeadlight, False)
			time.sleep( period )
			continue

		if headlight_power > 1.0 : headlight_power = 1.0
		if headlight_power < 0.0 : headlight_power = 0.0
		duty = headlight_power

		GPIO.output(pinHeadlight, True)
		time.sleep( period*duty );
		if duty < 1.0:
			GPIO.output(pinHeadlight, False)
			time.sleep( period*(1.0-duty) );


def move( powerL, powerR, t ):
	global power_left, power_right
	power_left  = powerL
	power_right = powerR
	time.sleep( t )
	power_left  = 0.0
	power_right = 0.0

pwm_headlight_thread  = threading.Thread( target=PWM_headlight_update_thread  )
pwm_left_thread  = threading.Thread( target=PWM_left_update_thread  )
pwm_right_thread = threading.Thread( target=PWM_right_update_thread )
pwm_headlight_thread.start()
pwm_left_thread.start()
pwm_right_thread.start()
last_tread_thread_start_time = time.time()

#=============================================================================

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:%s" % port)

print("Listening on port " + port + " ...")

# Video is streamed by separate process
video_stream_proc = None

#------------------------------
# StartVideoStream
#------------------------------
def StartVideoStream():
	global video_stream_proc
	subprocess.run('killall -9 libcamera-vid'.split()) # make sure stream is not running from someone else and don't be nice about it!
#	cmd = 'libcamera-vid -t 0 -n --listen --mode 1920:1080:8:U --codec h264 --flush --lores-width 0 -o tcp://0.0.0.0:7140'.split()
	cmd = 'libcamera-vid -t 0 -n --listen --mode 1920:1080:8:U --codec h264 --flush --lores-width 480 --framerate 12 -o tcp://0.0.0.0:7140'.split()
	print('Starting video stream with command:')
	print('   ' + ' '.join(cmd))
	video_stream_proc = subprocess.Popen( cmd )

StartVideoStream()


# Server loop
while not Done:
	#  Wait for next request from client
	command = socket.recv_string()
	print("Received request: " + command)
	if command.startswith('Hello'):
		mess = "Hola'!"

	elif command.startswith('quit'):
		Done = True
		mess = "Quitting ..."

	elif command.startswith('start_video_stream'):
		print(video_stream_proc)
		if video_stream_proc :
			mess = 'Video stream already started. Start request ignored'
		else:
			StartVideoStream()
			mess = 'Video stream started'

	elif command.startswith('stop_video_stream'):
		if video_stream_proc :
			print('Killing video stream process ' + str(video_stream_proc.pid) + ' ...')
			video_stream_proc.kill()
			time.sleep(1.0)
			mess = 'Video stream process ' + str(video_stream_proc.pid) + ' killed'
			video_stream_proc = None
		else:
			mess = 'Video stream not started. Stop request ignored'

	elif command.startswith('set_camera_angles'):
		[angleH, angleV] = command.split()[1:]
		mess = 'Setting camera angles to ' + angleH + ', ' + angleV
		servoH.value = float(angleH)
		servoV.value = float(angleV)

	elif command.startswith('stop_camera_servos'):
		mess = 'Stopping camera servos'
		servoH.detach()
		servoV.detach()

	elif command.startswith('set_emergency_pusher_angle'):
		angle_emergency_pusher = command.split()[1]
		mess = 'Setting emergency pusher angle to ' + angle_emergency_pusher
		servoEmergencyPusher.value = float(angle_emergency_pusher)

	elif command.startswith('stop_emergency_pusher_servo'):
		mess = 'Stopping emergency pusher servo'
		servoEmergencyPusher.detach()

	elif command.startswith('set_tread_power'):
		[powerL, powerR] = command.split()[1:]
		mess = 'Setting tread power to ' + powerL + ', ' + powerR
		power_left  = float(powerL)
		power_right = float(powerR)
		motors_stopped = False

	elif command.startswith('stop_motors'):
		motors_stopped = True
		mess = 'Stopping motors'

	elif command.startswith('set_laser_on'):
		GPIO.output(pinLaser, False)
		mess = "Laser on"

	elif command.startswith('set_laser_off'):
		GPIO.output(pinLaser, True)
		mess = "Laser off"

	elif command.startswith('set_headlight_on'):
		headlight_on = True
		mess = "Headlight on"

	elif command.startswith('set_headlight_off'):
		headlight_on = False
		mess = "Headlight off"

	elif command.startswith('set_headlight_power'):
		headlight_power = float(command.split()[1])
		mess = "Headlight power set to %f" % headlight_power

	elif command.startswith('reset_tread_threads'):
		now = time.time()
		if now - last_tread_thread_start_time < 3.0:
			mess = 'Tread threads restarted too recently. Ignoring'
		else:
			# tell threads to stop by setting Done to True, then join them,
			# then set Done back to False and restart them.
			Done = True
			pwm_headlight_thread.join()
			pwm_left_thread.join()
			pwm_right_thread.join()
			Done = False
			pwm_headlight_thread  = threading.Thread( target=PWM_headlight_update_thread  )
			pwm_left_thread  = threading.Thread( target=PWM_left_update_thread  )
			pwm_right_thread = threading.Thread( target=PWM_right_update_thread )
			pwm_headlight_thread.start()
			pwm_left_thread.start()
			pwm_right_thread.start()
			last_tread_thread_start_time = time.time()
			mess = "Tread threads restarted"

	else:
		mess = 'Unknown command: ' + command
	
	print(mess)
	socket.send_string(mess)

# Cleanup
pwm_headlight_thread.join()
pwm_left_thread.join()
pwm_right_thread.join()
GPIO.cleanup()
