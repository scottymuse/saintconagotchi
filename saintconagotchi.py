#!/usr/bin/python3

import pygame
import pyinotify

screen = pygame.display.set_mode((640,312))

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        img = pygame.image.load('/root/pwnagotchi.png')
        img = pygame.transform.scale(img, (640,312))
        screen.blit(img, (0,0))
        pygame.display.flip()

def main():
    pygame.init()
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    wdd = wm.add_watch('/root/pwnagotchi.png', mask)
    notifier.loop()

main()
