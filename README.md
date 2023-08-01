# crawlspacebot
Code for small robot built to examine my crawlspace

## Installation/setup

On the mac, make sure the ffmpeg and zmq packages are installed
~~~
brew install ffmpeg python-tk
python3 -m venv venv
source venv/bin/activate.csh
pip3 install zmq ffpyplayer
~~~


## Video stream from Raspberry Pi to mac
On raspberry Pi:
~~~
libcamera-vid -t 0 -n --listen --mode 1920:1080:8:U --codec h264 --flush --lores-width 0 -o tcp://0.0.0.0:8888
~~~

On Mac:
~~~
ffplay tcp://192.168.1.250:8888 -vf "setpts=N/30" -fflags nobuffer -flags low_delay -framedrop
~~~

## microSD card and raspberry Pi setup

Some instructions for setting up a new microSD card.

Use Raspberry Pi Imager program and select:

Raspberry Pi OS (32-bit)

You'll need to connect a keyboard, mouse, monitor and ethernet
get the WiFi network setup. Plug everything in and fire it up.
Here are some settings to use:

- I flipped the switch to make reduced desktop size so it
  fits better on the TV. The picture is still clipped, but
  it is more usable.

- I still use the old default user=pi pass=raspberry values
  and just ignore the complaints
  
- The ethernet will automatically connect without a password.
  The ethernet is only temporary since the BrosTrend USB WiFi
  adapter needs special drivers installed before it can work.

- After it does the initial updates and reboots, run

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

- The BrosTrend USB WiFi adapter needs special drivers installed.
  Follow the instructions at [https://https://linux.brostrend.com](https://linux.brostrend.com)
  which basically say to run the following command.<br>
  NOTE: This command takes a very long time to run and will appear to be
  stalled. Expect it to take 3/4 hour on a raspberry pi 2. Once the drivers
  are installed, you only need to set the WiFi country to US and then connect.
  (No need to reboot.)
~~~bash
sh -c 'wget linux.brostrend.com/install -O /tmp/install && sh /tmp/install'
~~~

- Install various software pieces. Note that the Add/Remove software tool
  is really slow at parsing the package list so avoid it if possible.
  NOTE: I downloaded VScode because it seemed a version was not available
  through apt, but later realized it was.
  NOTE: I don't actually need both code and arduino. Either will work.
  If using code, install the C++ and PlatformIO extensions.
  
  sudo pip install zmq
  sudo pip install Adafruit_GPIO
  sudo pip install Adafruit_SSD1306
  
  sudo apt install code
  sudo apt install spyder
  sudo apt install arduino
  sudo apt install cmake
  sudo pip install Adafruit_GPIO
  sudo pip install Adafruit_SSD1306
  sudo pip install adafruit-circuitpython-servokit

- Checkout the custom software:

  git clone https://github.com/faustus123/Tomm-I
  
  
- Add the following crontab:

  @reboot python3 /home/pi/Tomm-I/Tomm-I-v2/robot_statusd/robot_statusd.py


TROUBLESHOOTING:
--------------------
- I ran into a strange issue where the VNC desktop would start up OK but
  the menus would be short and the terminal windows would be very small.
  Rebooting did not seem to help. Logging out and back in did though. I
  was able to do this through the active VNC session.
