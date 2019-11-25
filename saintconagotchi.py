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
from LEDS import LEDS

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def process_IN_CLOSE_WRITE(self, event):
        self.callback()

# Thread to read logs and load queue
class read_pwnagotchi_log(threading.Thread):
    def __init__(self, log_generator, q_obj):
        threading.Thread.__init__(self)
        self.q_obj = q_obj
        self.log_generator = log_generator

    def run(self):
        for line in self.log_generator:
            if search(" sending association frame ", line):
                self.q_obj.put({"type": "activity", "time": time(), "act_type": "association"})
            elif search(" deauthing ", line):
                self.q_obj.put({"type": "activity", "time": time(), "act_type": "deauth"})
            elif search(" captured new handshake ", line):
                self.q_obj.put({"type": "activity", "time": time(), "act_type": "handshake"})
            elif search("activity -> excited", line):
                self.q_obj.put({"type": "mood", "time": time(), "mood_type": "excited"})
            elif search("activity -> bored", line):
                self.q_obj.put({"type": "mood", "time": time(), "mood_type": "bored"})
            elif search("activity -> sad", line):
                self.q_obj.put({"type": "mood", "time": time(), "mood_type": "sad"})
            elif search("activity -> lonely", line):
                self.q_obj.put({"type": "mood", "time": time(), "mood_type": "lonely"})
            elif search("unit is grateful", line):
                self.q_obj.put({"type": "mood", "time": time(), "mood_type": "grateful"})

# Thread to process queue
class process_log_queue(threading.Thread):
    def __init__(self, led_activity, led_mood, q_obj):
        threading.Thread.__init__(self)
        self.led_activity = led_activity
        self.led_mood = led_mood
        self.q_obj = q_obj
        self.leds = LEDS()

    def run(self):
        while(True):
            item = self.q_obj.get()
            if item["type"] == "activity":
                if self.led_activity:
                    if item["act_type"] == "association" and time() - item["time"] < .2:
                        self.leds.setColor(0, 255, 0, 0)
                    elif item["act_type"] == "deauth" and time() - item["time"] < .2:
                        self.leds.setColor(0, 0, 255, 0)
                    elif item["act_type"] == "handshake" and time() - item["time"] < .2:
                        self.leds.setColor(0, 0, 255, 255)
                    sleep(.2)
                    self.leds.off(0)
                else:
                    self.leds.off(0)
            elif item["type"] == "mood":
                if self.led.mood:
                    if item["mood_type"] == "excited":
                        self.leds.setColor(1, 255, 255, 0) #yellow
                    elif item["mood_type"] == "bored":
                        self.leds.setColor(1, 0, 255, 255) #purple
                    elif item["mood_type"] == "sad":
                        self.leds.setColor(1, 0, 0, 255) #blue
                    elif item["mood_type"] == "lonely":
                        self.leds.setColor(1, 255, 0, 255) #green
                    elif item["mood_type"] == "grateful":
                        self.leds.setColor(1, 192, 255, 203) #pink
                    elif item["mood_type"] == "unset":
                        self.leds.setColor(1, 128, 128, 128) #gray
            elif item["type"] == "led_toggle":
                if item["led"] == "activity":
                    self.led_activity = item["value"]
                else:
                    self.led_mood = item["value"]

class saintconagotchi:
    def __init__(self):
        self.screen = pygame.display.set_mode((640,480))
        self.led_mood = True
        self.led_activity = True
        self.manual_mode = False
        for proc in psutil.process_iter():
            if proc.name() == "pwnagotchi":
                if "--manual" in proc.cmdline():
                    self.manual_mode = True
                    break
                else:
                    break
        self.draw_status_squares()
        self.logfile = open("/var/log/pwnagotchi.log", "r")
        self.log_queue = queue.Queue()
        self.loglines = self.pwnagotchi_logfile_generator()
        self.read_logs_thread = read_pwnagotchi_log(log_generator=self.loglines, q_obj=self.log_queue)
        self.process_queue_thread = process_log_queue(led_activity=self.led_activity, led_mood=self.led_mood, q_obj=self.log_queue)

        pygame.init()
        pygame.mouse.set_visible(False)

        self.update_image() # Load the first image
        self.log_queue.put({"type":"mood", "time":time(), "mood_type":"unset"}) # Make the mood 'unset'

    def __del__(self):
        pygame.quit()

    def draw_status_squares(self):
        if self.led_activity:
            pygame.draw.rect(self.screen, (0, 255, 0), (0, 313, 213, 167))
        else:
            pygame.draw.rect(self.screen, (255, 0, 0), (0, 313, 213, 167))
        if self.manual_mode:
            pygame.draw.rect(self.screen, (255, 0, 0), (214, 313, 212, 167))
        else:
            pygame.draw.rect(self.screen, (0, 255, 0), (214, 313, 212, 167))
        if self.led_mood:
            pygame.draw.rect(self.screen, (0, 255, 0), (427, 313, 213, 167))
        else:
            pygame.draw.rect(self.screen, (255, 0, 0), (427, 313, 213, 167))
        pygame.display.flip()

    def start_image_watcher(self):
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

    # Pwnagotchi logfile generator
    def pwnagotchi_logfile_generator(self):
        self.logfile.seek(0,2)
        while True:
            line = self.logfile.readline()
            if not line:
                sleep(0.1)
                continue
            yield line

    def start_log_reader_thread(self):
        self.read_logs_thread.start()

    def start_queue_processor_thread(self):
        self.process_queue_thread.start()

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == K_ESCAPE: # To auto mode
                open('/root/.pwnagotchi-auto', 'x')
                psutil.Popen(["/bin/systemctl", "restart", "pwnagotchi"])
                self.manual_mode = False

            elif event.key == K_RETURN: # To manual mode
                psutil.Popen(["/bin/systemctl", "restart", "pwnagotchi"])
                self.manual_mode = True

            elif event.key == K_r:
                # Toggle LED activity notifications
                if self.led_activity:
                    self.led_activity = False
                else:
                    self.led_activity = True
                self.log_queue.put({"type": "led_toggle", "led": "activity", "value": self.led_activity})

            elif event.key == K_l:
                # Toggle mood LED
                if self.led_mood:
                    self.led_mood = False
                else:
                    self.led_mood = True
                self.log_queue.put({"type": "led_toggle", "led": "mood", "value": self.led_mood})

            self.draw_status_squares()

    #Loop to check for button presses
    def start_pygame_event_reader(self):
        while(True):
            for event in pygame.event.get():
                self.events(event)

if __name__ == "__main__":
    try:
        s = saintconagotchi()
        s.start_image_watcher()
        s.start_log_reader_thread()
        s.start_queue_processor_thread()
        s.start_pygame_event_reader()
    except Exception as e:
        print(e)
    finally:
        pygame.quit()
