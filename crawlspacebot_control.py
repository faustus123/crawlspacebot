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

host = "192.168.1.250"
port = "71400"

camera_angleH = 0.0
camera_angleV = 0.0
treadL = 0.0;
treadR = 0.0

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
cmd = 'ffplay tcp://192.168.1.250:71401 -vf "setpts=N/30" -fflags nobuffer -flags low_delay -framedrop'.split()
print('Launch video monitor with:')
print('   ' + ' '.join(cmd))
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
		gamepad = hid.device()
		gamepad.open(vendor_id, product_id)
		gamepad.set_nonblocking(True)
if not gamepad:
	print('Unable to find gamepad!')
else:
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
			if state['back']: camera_angleV = camera_angleH = 0.0
			if (last_camera_angleV!=camera_angleV) or (last_camera_angleH!=camera_angleH):
				socket.send_string('set_camera_angles %f %f' % (camera_angleH, camera_angleV))
				message = socket.recv_string()
			
			# Tank treads
			last_treadL = treadL
			last_treadR = treadR
			treadL = state['left_joy_V']
			treadR = state['right_joy_V']
			if (last_treadL!=treadL) or (last_treadR!=treadR):
				socket.send_string('set_tread_power %f %f' % (treadL, treadR))
				message = socket.recv_string()

			#print(state)

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
