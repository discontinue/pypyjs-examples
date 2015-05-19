from __future__ import absolute_import, print_function

import time
import js

WIDTH = 100# 640
HEIGHT = 50# 480


class Canvas(object):
    def __init__(self, width, height):
        self.canvas = self.create_canvas(width, height)
        self.context = self.canvas.getContext('2d')

        self.pixel = self.context.createImageData(1, 1)
        self.pixel_data = self.pixel.data

    def create_canvas(self, width, height):
        jquery = js.globals["$"]

        canvas = jquery("#canvasMandelbrot")[0] # Maybe started in the past?
        #if canvas == js.Undefined:
        if repr(canvas) == "<js.Undefined>":
            console = jquery("#console")
            console.before("""
                <canvas id="canvasMandelbrot" width="%i" height="%i"></canvas>
            """ % (width, height))
            canvas = jquery("#canvasMandelbrot")[0]
        return canvas

    def draw_pixel(self, x, y, r, g, b, alpha=255):
        self.context.fillStyle = 'rgba(%i,%i,%i,%i)' % (r,g,b,alpha)
        self.context.fillRect(x, y, 1, 1)


canvas = Canvas(WIDTH, HEIGHT)

LEFT = -2
RIGHT = 0.5
TOP = 1.25
BOTTOM = -1.25
ITERATIONS = 40
UPDATE_TIME = 0.75

next_update = time.time() + UPDATE_TIME
pixel_count = 0
total_count = HEIGHT * WIDTH
for y in range(HEIGHT):
    for x in range(WIDTH):
        z = complex(0, 0)
        c = complex(LEFT + x * (RIGHT - LEFT) / WIDTH, TOP + y * (BOTTOM - TOP) / HEIGHT)
        norm = abs(z) ** 2
        for count in xrange(ITERATIONS):
            if norm <= 4.0:
                z = z * z + c
                norm = abs(z * z)
            else:
                break

        if count <= 4:
            (r, g, b) = (128, 128, 128) # grey
        elif count <= 8:
            (r, g, b) = (0, 255, 0) # green
        elif count <= 10:
            (r, g, b) = (0, 0, 255) # blue
        elif count <= 12:
            (r, g, b) = (255, 0, 0) # red
        elif count <= 15:
            (r, g, b) = (255, 255, 0) # yellow
        else:
            (r, g, b) = (0, 0, 0) # black

        (r, g, b) = (count * 6, 0, 0)

        pixel_count += 1
        canvas.draw_pixel(x, y, r, g, b)

        if time.time()>next_update:
            next_update = time.time() + UPDATE_TIME
            print("%iPixels created" % pixel_count)