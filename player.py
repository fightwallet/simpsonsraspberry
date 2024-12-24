import os
import random
import time
import subprocess
from subprocess import PIPE, Popen, check_output
from evdev import InputDevice, ecodes
from select import select
import threading
import re

DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'videos')
TOUCH_DEVICE_PATH = '/dev/input/event0' 
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
STATIC_VIDEO = os.path.join(DIRECTORY, "../static.mp4") #add this file in the same directory as player.py

playProcess = None  # Track the current omxplayer process
audioProcess = None  # Track the audio playback process



def getVideos():
    to_play =  [
        os.path.join(DIRECTORY, file)
        for file in os.listdir(DIRECTORY)
        if file.lower().endswith('.mp4')
    ]
    random.shuffle(to_play) 
    return to_play



def playVideos():
    """Play videos with their respective start positions."""
    
    global playProcess
    background_layer = 0
    foreground_layer = 1

    while True:
        background_process = Popen(
            ['omxplayer', '--no-osd', '--aspect-mode', 'fill', '--layer', str(background_layer), '--loop', '--vol', '-6000', STATIC_VIDEO],
            stdin=PIPE
        )

        time.sleep(2)
        for video in getVideos():

            # Build the omxplayer command dynamically
            omx_command = ['omxplayer', '--no-osd', '--aspect-mode', 'fill', '--layer', str(foreground_layer), '--pos', '0', video]
            playProcess = Popen(omx_command, stdin=PIPE)
            playProcess.wait()


def monitor_touch():
    global playProcess
    touch_device = InputDevice(TOUCH_DEVICE_PATH)
    x_position = 0  # Initialize x_position with a default value

    while True:
        r, _, _ = select([touch_device], [], [], 0.5)
        if r:
            for event in touch_device.read():
                if event.type == ecodes.EV_ABS and event.code == ecodes.ABS_Y:
                    x_position = event.value  # Update x_position with touch data
                elif event.type == ecodes.EV_KEY and event.value == 0:
                    if x_position < SCREEN_WIDTH / 3:
                        send_command(b'\x1b[C', repeat=1)  # Forward
                    elif x_position > 2 * SCREEN_WIDTH / 3:
                        send_command(b'\x1b[D', repeat=1)  # Backward
                    else:
                        send_command(b'q')  # Quit

def send_command(command, repeat=1, delay=0.05):
    global playProcess
    if playProcess and playProcess.poll() is None:
        for _ in range(repeat):
            playProcess.stdin.write(command)
            playProcess.stdin.flush()
            time.sleep(delay)

# Start touch monitoring thread
touch_thread = threading.Thread(target=monitor_touch)
touch_thread.daemon = True
touch_thread.start()

playVideos()
