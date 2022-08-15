# crawlspacebot
Code for small robot built to examine my crawlspace

## Installation/setup

On the mac, make sure the ffmpeg and zmq packages are installed
~~~
brew install ffmpeg
python3 -m venv venv
source venv/bin/activate.csh
pip3 install zmq
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
