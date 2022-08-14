#!/usr/bin/env python3

from gpiozero import Servo
import time

pinH = 20
pinV = 21

servoH = Servo( pinH )
servoV = Servo( pinV )

servoH.mid()
servoV.mid()
time.sleep(2)

