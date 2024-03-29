# crawlspacebot
Code for small robot built to examine my crawlspace

## Installation/setup

### microSD card and raspberry Pi inital setup

Use Raspberry Pi Imager program and select:

Raspberry Pi OS (32-bit)

Go to the settings and enter username/password, WiFi
SSID/password, locale, timezone, etc. This will save 
you from having to connect to the external monitor,
keyboard, mouse to set this stuff up.

Once the microSD is written to, put it in the RPi and
boot it up.

You will need to look at the WiFi router to find the
IP address of the RPi. Then you should be able to 
log into it via ssh. Run:

  "sudo raspi-config"

  Apply the following settings:

  Display Options -> VNC Resolution -> 1920x1080<br>
  Interface Options -> SSH -> enabled<br>
  Interface Options -> VNC -> enabled<br>
  Interface Options -> I2C -> enabled<br>
  Interface Options -> Serial -> disable login shell over serial<br>
  Interface Options -> Serial -> enable serial port hardware<br>

  NOTE: You must reboot after changing the settings since the /dev/ttyS0
        device won't be there until the serial option was enabled.

- At this point you should be able to switch to VNC for connecting and
  can disconnect the monitor, keyboard, mouse from the RPi.

- Install various software pieces. Note that the Add/Remove software tool
  is really slow at parsing the package list so avoid it if possible.
  NOTE: I downloaded VScode because it seemed a version was not available
  through apt, but later realized it was.
  NOTE: I don't actually need both code and arduino. Either will work.
  If using code, install the C++ and PlatformIO extensions.

  sudo apt install -y nedit<br>
  sudo pip install zmq<br>
  sudo pip install Adafruit_GPIO<br>
  sudo pip install Adafruit_SSD1306<br>

- Checkout the custom software in the home directory of the pi account:

  git clone https://github.com/faustus123/crawlspacebot
  
  
- Setup the crontab to automatically start the robot control program:

  crontab crawlspacebot/crontab.pi

  This should setup a crontab with the following line:
  @reboot python3 /home/pi/crawlspacebot/crawlspacebot.py

On the mac, make sure the ffmpeg and zmq packages are installed
~~~
brew install ffmpeg python-tk
python3 -m venv venv
source venv/bin/activate.csh
pip3 install zmq ffpyplayer
~~~


### Video stream from Raspberry Pi to mac
The `crawlspacebot.py` script that is automatically run by the
crontab above will automatically start the video stream server
with a command similar to this:
~~~
libcamera-vid -t 0 -n --listen --mode 1920:1080:8:U --codec h264 --flush --lores-width 0 -o tcp://0.0.0.0:8888
~~~

On Mac:
~~~
ffplay tcp://192.168.1.250:8888 -vf "setpts=N/30" -fflags nobuffer -flags low_delay -framedrop
~~~




TROUBLESHOOTING:
--------------------
- I ran into a strange issue where the VNC desktop would start up OK but
  the menus would be short and the terminal windows would be very small.
  Rebooting did not seem to help. Logging out and back in did though. I
  was able to do this through the active VNC session.
