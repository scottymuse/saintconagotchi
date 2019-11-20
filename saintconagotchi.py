#!/usr/bin/python3

import pygame
from pygame.locals import *
import pyinotify
import psutil
from subprocess import PIPE
from time import time,sleep
from re import search
import queue
import threading
import board
import neopixel

screen = pygame.display.set_mode((640,480))
strip = neopixel.NeoPixel(pin=board.D18, n=2)
led_mood = True
led_activity = True

pygame.init()

def update_image():
    img = pygame.image.load('/root/pwnagotchi.png')
    img = pygame.transform.scale(img, (640,312))
    screen.blit(img, (0,0))
    pygame.display.flip()

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        update_image()

def events(event):
    global led_mood
    global led_activity
    if event.type == pygame.KEYDOWN:
        if event.key == K_ESCAPE: # To auto mode
            open('/root/.pwnagotchi-auto', 'x')
            psutil.Popen(["/bin/systemctl", "restart", "pwnagotchi"])
        if event.key == K_RETURN: # To manual mode
            psutil.Popen(["/bin/systemctl", "restart", "pwnagotchi"])

        if event.key == K_r:
            # Toggle LED activity notifications
            if led_activity:
                led_activity = False
                strip[0] = (0, 0, 0)
            else:
                led_activity = True

        #if event.key == K_l:
            # Toggle mood LED
            if led_mood:
                led_mood = False
                strip[1] = (0, 0, 0)
            else:
                led_mood = True

update_image() # Load the first image

# Thread to watch the image for changes and update
wm = pyinotify.WatchManager()
mask = pyinotify.IN_CLOSE_WRITE
notifier = pyinotify.ThreadedNotifier(wm, EventHandler())
notifier.start()
wdd = wm.add_watch('/root/pwnagotchi.png', mask)

# Pwnagotchi logfile generator
def pwnagotchi_logfile_reader(logfile):
    logfile.seek(0.2)
    while True:
        line = logfile.readline()
        if not line:
            sleep(0.1)
            continue
        yield line

logfile = open("/var/log/pwnagotchi.log")
loglines = pwnagotchi_logfile_reader(logfile)

# Thread to read logs and load queue
class read_pwnagotchi_log(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        for line in loglines:
            if search(" deauthing ", line):
                # get AP name maybe for screen?
                log_queue.put({"type":"deauth", "time":time()})
            if search(" sending association frame ", line):
                # get AP name maybe for screen?
                log_queue.put({"type":"association", "time":time()})
            #need to understand ai mood better

# Thread to process queue
#make the queue
log_queue = queue.Queue()
class process_log_queue(threading.Thread):
    def __init__(self, q_obj):
        threading.Thread.__init__(self)
        self.q_obj = q_obj

    def run(self):
        while(True):
            item = self.q_obj.get()
            if item["type"] == "deauth" and led_activity and time() - item["time"] < .2:
                strip[0] = (0, 255, 0)
                sleep(.2)
                strip[0] = (0, 0, 0)
            if item["type"] == "association" and led_activity and time() - item["time"] < .2:
                strip[0] = (255, 0, 0)
                sleep(.2)
                strip[0] = (0, 0, 0)

read_logs_thread = read_pwnagotchi_log()
read_logs_thread.start()
process_queue_thread = process_log_queue(log_queue)
process_queue_thread.start()

#Loop to check for button presses
while(True):
    for event in pygame.event.get():
        events(event)


