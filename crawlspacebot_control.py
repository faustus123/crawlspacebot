#!/usr/bin/env python3
#
#  Run this on the mac
#

import zmq
import time
import sys

host = "192.168.1.250"
port = "71400"

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.bind("tcp://{}:{}".format(host, port))

# Send initial handshake message
print('Sending handshake command "Hello"')
socket.send ('Hello')
message = socket.recv()
print('Recieved: "' + message + '"')


