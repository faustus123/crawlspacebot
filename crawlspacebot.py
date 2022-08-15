#!/usr/bin/env python3
#
#  Run this on the robot (raspberry pi)
#

import zmq
import time
import sys
import subprocess
import threading
import RPi.GPIO as GPIO
from gpiozero import Servo


port = "71400"  # For zmq commands
Done = False

# Camera angle servo control
pinH = 20
pinV = 21

servoH = Servo( pinH )
servoV = Servo( pinV )
servoH.mid()
servoV.mid()

# tread DC motor control
pinA = 23
pinB = 24
pinC = 27
pinD = 22

freq = 7500  # cycle frequency
period = 1.0/freq

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
	cmd = 'libcamera-vid -t 0 -n --listen --mode 1920:1080:8:U --codec h264 --flush --lores-width 0 -o tcp://0.0.0.0:7140'.split()
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

	elif command.startswith('set_tread_power'):
		[powerL, powerR] = command.split()[1:]
		mess = 'Setting tread power to ' + powerL + ', ' + powerR
		power_left  = float(powerL)
		power_right = float(powerR)

	else:
		mess = 'Unknown command: ' + command
	
	print(mess)
	socket.send_string(mess)

# Cleanup
pwm_left_thread.join()
pwm_right_thread.join()
GPIO.cleanup()
