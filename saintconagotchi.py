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

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def process_IN_CLOSE_WRITE(self, event):
        self.callback()

#LED Class
class LEDS():
    def __init__(self):
        self.s = neopixel.NeoPixel(pin=board.D18, n=2)

    def setColor(self, led, g, r, b):
        self.s[led] = (g, r, b)

    def off(self, led):
        self.s[led] = (0, 0, 0)


# Thread to read logs and load queue
class read_pwnagotchi_log(threading.Thread):
    def __init__(self, q_obj):
        threading.Thread.__init__(self)
        self.q_obj = q_obj

    def run(self):
        for line in loglines:
            if search(" deauthing ", line):
                # get AP name maybe for screen?
                q_obj.put({"led": "activity", "type":"deauth", "time":time()})
            if search(" sending association frame ", line):
                # get AP name maybe for screen?
                q_obj.put({"led": "activity", "type":"association", "time":time()})
            #need to understand ai mood better

# Thread to process queue
class process_log_queue(threading.Thread):
    def __init__(self, q_obj):
        threading.Thread.__init__(self)
        self.q_obj = q_obj
        self.leds = LEDS()

    def run(self):
        while(True):
            item = self.q_obj.get()
            if item["led"] == "activity":
                if led_activity:
                    if item["type"] == "deauth" and time() - item["time"] < .2:
                        self.leds.setColor(0, 0, 255, 0)
                        sleep(.2)
                        self.leds.off(0)
                    elif item["type"] == "association" and time() - item["time"] < .2:
                        self.leds.setColor(0, 255, 0, 0)
                        sleep(.2)
                        self.leds.off(0)
                else:
                    self.leds.off(0)

class saintconagotchi:
    def __init__(self):
        self.screen = pygame.display.set_mode((640,480))
        self.led_mood = True
        self.led_activity = True
        self.logfile = open("/var/log/pwnagotchi.log", "r")
        self.log_queue = queue.Queue()
        self.read_logs_thread = read_pwnagotchi_log(self.log_queue)
        self.process_queue_thread = process_log_queue(self.log_queue)

        pygame.init()
        pygame.mouse.set_visible(False)

        update_image() # Load the first image

    def start_image_watcher():
        # Thread to watch the image for changes and update
        wm = pyinotify.WatchManager()
        mask = pyinotify.IN_CLOSE_WRITE
        notifier = pyinotify.ThreadedNotifier(wm, EventHandler(callback=self.update_image))
        notifier.start()
        wdd = wm.add_watch('/root/pwnagotchi.png', mask)

    def update_image(self):
        img = pygame.image.load('/root/pwnagotchi.png')
        img = pygame.transform.scale(img, (640,312))
        self.screen.blit(img, (0,0))
        pygame.display.flip()

    def start_logfile_generator():
        self.loglines = pwnagotchi_logfile_generator()

    # Pwnagotchi logfile generator
    def pwnagotchi_logfile_generator():
        self.logfile.seek(0,2)
        while True:
            line = self.logfile.readline()
            if not line:
                sleep(0.1)
                continue
            yield line

    def start_log_reader_thread():
        read_logs_thread.start()

    def start_queue_processor_thread():
        process_queue_thread.start()

    def events(event):
        if event.type == pygame.KEYDOWN:
            if event.key == K_ESCAPE: # To auto mode
                open('/root/.pwnagotchi-auto', 'x')
                psutil.Popen(["/bin/systemctl", "restart", "pwnagotchi"])

            elif event.key == K_RETURN: # To manual mode
                psutil.Popen(["/bin/systemctl", "restart", "pwnagotchi"])

            elif event.key == K_r:
                # Toggle LED activity notifications
                if self.led_activity:
                    self.led_activity = False
                else:
                    self.led_activity = True

            elif event.key == K_l:
                # Toggle mood LED
                if self.led_mood:
                    self.led_mood = False
                else:
                    self.led_mood = True

    #Loop to check for button presses
    def start_pygame_event_reader():
        while(True):
            for event in pygame.event.get():
                events(event)

if __name__ == "__main__":
    s = saintconagotchi()
    s.start_image_watcher()
    s.start_logfile_generator()
    s.start_log_reader_thread()
    s.start_queue_processor_thread()
    s.start_pygame_event_reader()
