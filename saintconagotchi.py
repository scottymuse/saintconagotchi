#!/usr/bin/python3

import pygame
from pygame.locals import *
import pyinotify
import psutil
from subprocess import PIPE
from time import time
import board
import neopixel

screen = pygame.display.set_mode((640,480))
strip = neopixel.Neopixel(pin=board.D18, n=2)

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        img = pygame.image.load('/root/pwnagotchi.png')
        img = pygame.transform.scale(img, (640,312))
        screen.blit(img, (0,0))
        pygame.display.flip()

def events(event):
    if event.type == pygame.KEYDOWN:
        if event.key == K_ESCAPE:
            # Toggle Manual/Auto Mode
            #touch /root/.pwnagotchi-auto && systemctl restart pwnagotchi
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
            if to_auto:
                open('/root/.pwnagotchi-auto')
            psutil.Popen(["/bin/systemctl", "restart", "pwnagotchi"])

        #if event.key == K_r:
            # Toggle LED activity notifications
        #if event.key == K_l:
            # Toggle mood LED

def main():
    pygame.init()
    
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE
    notifier = pyinotify.ThreadedNotifier(wm, EventHandler())
    notifier.start()
    wdd = wm.add_watch('/root/pwnagotchi.png', mask)

    while True:
        for event in pygame.event.get():
            events(event)


main()
