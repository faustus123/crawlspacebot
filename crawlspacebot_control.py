#!/usr/bin/env python3
#
#  Run this on the mac
#

import zmq
import time
import sys
import os
import subprocess
import hid

host = "192.168.1.240"
port = "71400"

if len(sys.argv) > 1:
	host = sys.argv[1]
	print("Setting host to: %s" % host)


camera_angleH_center =  0.208
camera_angleV_center = -0.310
camera_angleH = camera_angleH_center
camera_angleV = camera_angleV_center
treadL = 0.0;
treadR = 0.0
laserOn = False
headlightOn = False
headlightPower = 0.5
emergency_pusher_parked = -0.89
emergency_pusher_full   = 0.65
emergency_pusher_angle  = emergency_pusher_parked

def LogitechReportToState( report ):
	state = {}
	state['left_joy_H'] = max( (float(report[0])-128.0)/127.0, -1.0)
	state['left_joy_V'] = max( (float(report[1])-128.0)/127.0, -1.0)
	state['right_joy_H'] = max( (float(report[2])-128.0)/127.0, -1.0)
	state['right_joy_V'] = max( (float(report[3])-128.0)/127.0, -1.0)
	dpad = report[4] & 0b00001111
	state['dpad_up'   ] = (dpad==0) or (dpad==1) or (dpad==7)
	state['dpad_down' ] = (dpad==3) or (dpad==4) or (dpad==5)
	state['dpad_left' ] = (dpad==5) or (dpad==6) or (dpad==7)
	state['dpad_right'] = (dpad==1) or (dpad==2) or (dpad==3)
	state['button_X'] = (report[4] & 0b00010000) != 0
	state['button_A'] = (report[4] & 0b00100000) != 0
	state['button_B'] = (report[4] & 0b01000000) != 0
	state['button_Y'] = (report[4] & 0b10000000) != 0
	state['bumper_left'  ] = (report[5] & 0b00000001) != 0
	state['bumper_right' ] = (report[5] & 0b00000010) != 0
	state['trigger_left' ] = (report[5] & 0b00000100) != 0
	state['trigger_right'] = (report[5] & 0b00001000) != 0
	state['back'         ] = (report[5] & 0b00010000) != 0
	state['start'        ] = (report[5] & 0b00100000) != 0
	state['L3'           ] = (report[5] & 0b01000000) != 0
	state['R3'           ] = (report[5] & 0b10000000) != 0
	return state


# Connect to robot
context = zmq.Context()
socket = context.socket(zmq.REQ)
bind_addr = "tcp://{}:{}".format(host, port)
print( 'Binding to: ' + bind_addr)
socket.connect(bind_addr)

# Send initial handshake message
print('Sending handshake command "Hello"')
socket.send_string('Hello')
message = socket.recv_string()
print('Recieved: "' + message + '"')

# Initialize camera angles
socket.send_string('set_camera_angles %f %f' % (camera_angleH, camera_angleV))
message = socket.recv_string()

# Initialize emergency pusher
socket.send_string('set_emergency_pusher %f' % (emergency_pusher_angle))
message = socket.recv_string()

# Initialize treads to stopped
socket.send_string('set_tread_power %f %f' % (treadL, treadR))
message = socket.recv_string()

# Start video stream on robot
socket.send_string('start_video_stream')
message = socket.recv_string()
print(message)

# Open video window to receive stream
# n.b. For some reason, running this command with Popen returns a message about
# not being able to connect to server and will not open the display window.
# cmd = 'ffplay tcp://'+host+':7140 -vf "setpts=N/30" -fflags nobuffer -flags low_delay -framedrop'
cmd = 'ffplay tcp://'+host+':7140 -fflags nobuffer -flags low_delay -framedrop'
print('Please launch video monitor with:')
print('   ' + ' '.join(cmd.split()))
video_stream_proc = None
#video_stream_proc = subprocess.Popen(cmd)

# Setup HID (game controller)
# Find Logitech device
vendor_id = 0x0
product_id = 0x0
gampad = None
state = None
for d in hid.enumerate():
	if d['product_string'] == 'Logitech Dual Action':
		vendor_id  = int(d['vendor_id' ])
		product_id = int(d['product_id'])
		print('Found Logictech gamepad: vendor_id:0x%x product_id:0x%x' % (vendor_id, product_id))
		gamepad = hid.Device(vid=vendor_id, pid=product_id)
		gamepad.nonblocking = True
#		gamepad = hid.device()
#		gamepad.open(vendor_id, product_id)
#		gamepad.set_nonblocking(True)
if not gamepad:
	print('Unable to find gamepad!')
else:
	last_R3 = False
	last_L3 = False
	while True:
		report = gamepad.read(512)
		if report:
			state = LogitechReportToState(report)
		if state:
			
			# Camera angle
			last_camera_angleV = camera_angleV
			last_camera_angleH = camera_angleH
			if state['dpad_up'   ]: camera_angleV -= 0.002
			if state['dpad_down' ]: camera_angleV += 0.002
			if state['dpad_left' ]: camera_angleH += 0.002
			if state['dpad_right']: camera_angleH -= 0.002
			camera_angleV = max(-1.0, min( camera_angleV, 1.0))
			camera_angleH = max(-1.0, min( camera_angleH, 1.0))
			if state['back']:
				# Remember current camera angles as "center"
				camera_angleV_center =  camera_angleV
				camera_angleH_center =  camera_angleH
			if (last_L3 != state['L3']) and (last_L3 == False):
				# Move camera angles to "center"
				camera_angleV = camera_angleV_center
				camera_angleH = camera_angleH_center
			last_L3 = state['L3']
			if (last_camera_angleV!=camera_angleV) or (last_camera_angleH!=camera_angleH):
				# Send command to robot iff camera angles have changed
				socket.send_string('set_camera_angles %f %f' % (camera_angleH, camera_angleV))
				message = socket.recv_string()

			# Emergency pusher angle
			last_emergency_pusher_angle = emergency_pusher_angle
			if state['button_Y']: emergency_pusher_angle += 0.03
			if state['button_A']: emergency_pusher_angle -= 0.03
			emergency_pusher_angle = max(emergency_pusher_parked, min( emergency_pusher_angle, emergency_pusher_full))
			if last_emergency_pusher_angle != emergency_pusher_angle :
				socket.send_string('set_emergency_pusher_angle %f' % (emergency_pusher_angle))
				message = socket.recv_string()
				time.sleep(0.020)
				if emergency_pusher_angle == emergency_pusher_parked:
					socket.send_string('stop_emergency_pusher_servo')
					message = socket.recv_string()

			# Laser
			if state['button_B'] != laserOn :
				laserOn = state['button_B']
				if laserOn:
					socket.send_string('set_laser_on')
				else:
					socket.send_string('set_laser_off')
				message = socket.recv_string()
			
			# Headlight
			if (last_R3 != state['R3']) and (last_R3 == False):
				headlightOn = not headlightOn
				if headlightOn:
					socket.send_string('set_headlight_on')
				else:
					socket.send_string('set_headlight_off')
				message = socket.recv_string()
			last_R3 = state['R3']
#			if state['R3'] and not headlightOn:
#				socket.send_string('set_headlight_on')
#				headlightOn = True
#				message = socket.recv_string()
#			if state['L3'] and headlightOn:
#				socket.send_string('set_headlight_off')
#				headlightOn = False
#				message = socket.recv_string()
			last_headlightPower = headlightPower
			if state['bumper_right']: headlightPower += 0.01
			if state['bumper_left' ]: headlightPower -= 0.01
			headlightPower = max(0.0, min( headlightPower, 1.0))
			if headlightPower != last_headlightPower:
				socket.send_string('set_headlight_power %f' % headlightPower)
				message = socket.recv_string()
			
			# Tank treads
			last_treadL = treadL
			last_treadR = treadR
			treadL = -state['left_joy_V']
			treadR = -state['right_joy_V']
			
			# Deadband so wheels don't turn when joystick close to middle
			deadband = 0.1
			if abs(treadL) < deadband : treadL = 0.0
			if abs(treadR) < deadband : treadR = 0.0
			
			# Left trigger forces motors to sync so we go straight forward/backward
			if state['trigger_left']:
				asym = treadR
				treadR = treadL + asym
				treadL = treadL - asym
			
			# Right trigger goes at fast speed. Otherwise, go slow
			if not state['trigger_right']:
				treadR = treadR / 4.0
				treadL = treadL / 4.0
			
			# If tread power has changed since last time, send new values.
			if (last_treadL!=treadL) or (last_treadR!=treadR):
				# If tread power for both is zero, tell PWM to stop
				# Otherwise send new motor values
				if (treadL==0.0) and (treadR==0.0):
					socket.send_string('stop_motors')
					message = socket.recv_string()
				else:
					socket.send_string('set_tread_power %f %f' % (treadL, treadR))
					message = socket.recv_string()

			# Stop all motors (stops sending PWM, motors will start as soon as new values sent)
			if state['button_X']:
				socket.send_string('stop_camera_servos')
				message = socket.recv_string()
				socket.send_string('stop_motors')
				message = socket.recv_string()

			# Tell tread threads and video to restart (in case one becomes non-responsive)
			if state['start']:
				socket.send_string('reset_tread_threads')
				message = socket.recv_string()
				print(message)
#				socket.send_string('stop_video_stream')
#				message = socket.recv_string()
#				print(message)
				socket.send_string('change_video_mode')
				message = socket.recv_string()
				print(message)
#				time.sleep(1.5)
#				socket.send_string('start_video_stream')
#				message = socket.recv_string()
				

			if message : print(message)
			message = None

#for i in range(-100,101, 1):
#	angleH = i/100.0
#	socket.send_string('set_camera_angles ' + str(angleH) + ' 0.0')
#	message = socket.recv_string()
#	time.sleep(0.1)
#socket.send_string('set_camera_angles 0.0 0.0')
#message = socket.recv_string()
#
#for i in range(-100,101, 1):
#	angleV = i/100.0
#	socket.send_string('set_camera_angles 0.0 ' + str(angleV))
#	message = socket.recv_string()
#	time.sleep(0.05)
#socket.send_string('set_camera_angles 0.0 0.0')
#message = socket.recv_string()



# Close video monitor
if video_stream_proc:
	video_stream_proc.kill()
