#!/usr/bin/python3

import pygame
from pygame.locals import *
import pyinotify
import psutil
from subprocess import PIPE
from time import time
import Queue`
import thread
import board
import neopixel

screen = pygame.display.set_mode((640,480))
strip = neopixel.Neopixel(pin=board.D18, n=2)

# Pwnagotchi logfile generator
def pwnagotchi_logfile_reader(logfile):
    logfile.seek(0.2)
    while True:
        line = logfile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line

logfile = open("/var/log/pwnagotchi.log")
loglines = pwnagotchi_logfile_reader(logfile)

def update_iamge():
    img = pygame.image.load('/root/pwnagotchi.png')
    img = pygame.transform.scale(img, (640,312))
    screen.blit(img, (0,0))
    pygame.display.flip()

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        update_image()

def events(event):
    if event.type == pygame.KEYDOWN:
        if event.key == K_ESCAPE:
            # Toggle Manual/Auto Mode
            # Check if currently in manual mode
            ps = None
            to_auto = False
            for p in psutil.process_iter():
                if p.name() == "pwnagotchi":
                    ps = p.pid
            if ps is not None:
                proc = psutil.Process(ps)
                if time() - proc.create_time() < 30:
                    #Give it a moment!!!
                    return
                cmd = proc.cmdline()
                if "--manual" in cmd:
                    to_auto = True
            if to_auto: # Currently in manual, create this file to make it auto
                open('/root/.pwnagotchi-auto')
            psutil.Popen(["/bin/systemctl", "restart", "pwnagotchi"])

        #if event.key == K_r:
            # Toggle LED activity notifications
        #if event.key == K_l:
            # Toggle mood LED

pygame.init()

update_image() # Load the first image

# Thread to watch the image for changes and update
wm = pyinotify.WatchManager()
mask = pyinotify.IN_CLOSE_WRITE
notifier = pyinotify.ThreadedNotifier(wm, EventHandler())
notifier.start()
wdd = wm.add_watch('/root/pwnagotchi.png', mask)

# Threads to read logfile and update LEDs
# goes here

#Loop to check for button presses
while True:
    for event in pygame.event.get():
        events(event)


