# pylint: disable=redefined-outer-name,global-statement

import time
import math
from random import randint
import board
import neopixel
from adafruit_debouncer import Debouncer

# various colors
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
MAGENTA = (255, 0, 255)
PINK = (255, 128, 128)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


# ------------------------------------------------------------
# Setup hardware

pixel_pin = board.A1
num_pixels = 38
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=1.0, auto_write=False)

debouncers = []

inner_fire_switch = Debouncer(board.D7)
debouncers.append(inner_fire_switch)

flame_switch = Debouncer(board.D9)
debouncers.append(flame_switch)

magic_circle_switch = Debouncer(board.D10)
debouncers.append(magic_circle_switch)

magic_circle_flash_switch = Debouncer(board.D11)
debouncers.append(magic_circle_flash_switch)

magic_circle_white_switch = Debouncer(board.D12)
debouncers.append(magic_circle_white_switch)


# ------------------------------------------------------------
# Utilities

def clip(value):
    return min(255, max(0, int(value)))


# ------------------------------------------------------------
# Class to manage the magic circle

class MagicCircle(object):


    def __init__(self, base_color, pixel_range, update_interval, flash_one_of):
        self._flash_colors = [PINK, YELLOW, WHITE, RED, MAGENTA]
        self._interval = update_interval
        self._color = base_color
        self._pixel_range = pixel_range
        self._target = 0
        self._flash_one_of = flash_one_of
        self._current_brightness = 0.0
        self._brightness_delta = math.pi / 50
        self._enabled = False
        self._flash_enabled = False


    def enable(self, on_off):
        self._enabled = on_off


    def enable_flash(self, on_off):
        self._flash_enabled = on_off


    def update(self, now, all_white):
        if now < self._target:
            return                            #not time to update yet

        self._target = now + self._interval

        self._current_brightness += self._brightness_delta
        if self._current_brightness >= 2 * math.pi:
            self._current_brightness = 0.0

        if self._enabled:
            if all_white:
                c = WHITE
            elif self._flash_enabled and randint(0, self._flash_one_of) == 0:
                c = self._flash_colors[randint(0, len(self._flash_colors) - 1)]
            else:
                scale = (math.sin(self._current_brightness) + 1.0) / 2.0
                c = [clip(x * scale) for x in self._color]
        else:
            c = BLACK

        for p in self._pixel_range:
            pixels[p] = c


# ------------------------------------------------------------
# Class to manage the inner fire

class InnerFire(object):

    def __init__(self, pixel_range, update_interval):
        self._colors = [(255, 0, 0), (220, 0, 0), (192, 0, 0), (128, 0, 0), (64, 0, 0), (0, 0, 0)]
        self._pixel_range = pixel_range
        self._interval = update_interval
        self._target = 0
        self._enabled = False


    def enable(self, on_off):
        self._enabled = on_off


    def update(self, now):
        if now < self._target:
            return

        self._target = now + self._interval

        for p in self._pixel_range:
            if self._enabled:
                pixels[p] = self._colors[randint(0, len(self._colors) - 1)]
            else:
                pixels[p] = BLACK


# ------------------------------------------------------------
# Class to manage the flame

class Flame(object):

    def __init__(self, pixel_range, update_interval, flash_one_of):
        self._flame_colors = [(192, 0, 255), (128, 0, 255), (128, 0, 128), (255, 0, 128), (64, 0, 255)]
        self._flash_colors = [WHITE, RED, BLUE, MAGENTA]
        self._pixel_range = pixel_range
        self._interval = update_interval
        self._flash_one_of = flash_one_of
        self._target = 0
        self._enabled = False


    def enable(self, on_off):
        self._enabled = on_off


    def update(self, now):
        if now < self._target:
            return

        self._target = now + self._interval

        if self._enabled:
            if randint(0, self._flash_one_of) == 0:
                flash_color = self._flash_colors[randint(0, len(self._flash_colors) - 1)]
                for p in self._pixel_range:
                    pixels[p] = flash_color
            else:
                for p in self._pixel_range:
                    pixels[p] = self._flame_colors[randint(0, len(self._flame_colors) - 1)]
        else:
            for p in self._pixel_range:
                pixels[p] = BLACK


# pixel ranges
magic_circle_pixels = range(0, 24)
inner_fire_pixels = range(24, 31)
flame_pixels = range(31, 38)

# Magic circle settings
magic_circle_color = RED
magic_circle_interval = 0.05
magic_circle_flash_range = 25

# Inner fire settings
inner_fire_interval = 0.1

# Flame settings
flame_interval = 0.05
flame_flash_range = 10

magic_circle = MagicCircle(RED, magic_circle_pixels, magic_circle_interval, magic_circle_flash_range)
inner_fire = InnerFire(inner_fire_pixels, inner_fire_interval)
flame = Flame(flame_pixels, flame_interval, flame_flash_range)

while True:
    now = time.monotonic()
    for debouncer in debouncers:
        debouncer.update()

    magic_circle.enable(magic_circle_switch.value)
    magic_circle.enable_flash(magic_circle_flash_switch.value)
    flame.enable(flame_switch.value)
    inner_fire.enable(inner_fire_switch.value)

    magic_circle.update(now, not magic_circle_white_switch.value)
    flame.update(now)
    inner_fire.update(now)
    pixels.show()
