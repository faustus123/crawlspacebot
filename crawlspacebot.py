#!/usr/bin/env python3
#
#  Run this on the robot (raspberry pi)
#

import zmq
import time
import sys

port = "71400"

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:%s" % port)


while True:
    #  Wait for next request from client
    message = socket.recv()
    print "Received request: ", message
    if message.startswith('Hello'):
		    socket.send("Hola'")

