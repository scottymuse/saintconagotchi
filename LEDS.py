import board
import neopixel


class LEDS(): 
    def __init__(self): 
        self.s = neopixel.NeoPixel(pin=board.D18, n=2) 
 
    def __del__(self): 
        self.s.deinit() 
 
    def setColor(self, led, g, r, b): 
        self.s[led] = (g, r, b) 
 
    def off(self, led): 
        self.s[led] = (0, 0, 0)

