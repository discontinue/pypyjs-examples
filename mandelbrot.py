from __future__ import absolute_import, print_function

import time

import js

class Canvas(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.canvas = self.create_canvas()
        self.context = self.canvas.getContext('2d')

        self.pixel = self.context.createImageData(1, 1)
        self.pixel_data = self.pixel.data

    def create_canvas(self):
        jquery = js.globals["$"]

        canvas = jquery("#canvasMandelbrot")[0] # Maybe started in the past?
        if canvas == js.undefined:
            console = jquery("#output")
            console.before("""
                <canvas id="canvasMandelbrot" width="%i" height="%i"></canvas>
            """ % (self.width, self.height))
            canvas = jquery("#canvasMandelbrot")[0]
        return canvas

    def draw_pixel(self, x, y, r, g, b, alpha=255):
        self.context.fillStyle = 'rgba(%i,%i,%i,%i)' % (r, g, b, alpha)
        self.context.fillRect(x, y, 1, 1)


class Mandelbrot(object):
    def __init__(self, canvas, left, right, top, bottom, iterations):
        self.canvas = canvas
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.iterations = iterations

        self.width = self.canvas.width
        self.height = self.canvas.height

        self.y = 0
        self.last_update = self.start_time = time.time()
        self.last_pos = 0

        self.done = False

    def render_mandelbrot_line(self):
        self.y += 1
        if self.y >= self.height:
            if not self.done:
                self.done = True
                duration = time.time() - self.start_time
                msg = "%ix%ipx Rendered in %iSec." % (self.width, self.height, duration)
                print(msg)
                print(" --- END --- ")
            return

        for x in range(self.width):
            z = complex(0, 0)
            c = complex(
                self.left + x * (self.right - self.left) / self.width,
                self.top + self.y * (self.bottom - self.top) / self.height
            )
            norm = abs(z) ** 2
            for count in xrange(self.iterations):
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

            canvas.draw_pixel(x, self.y, r, g, b)

    def display_stats(self):
        pos = (self.y * self.width)
        pos_diff = pos - self.last_pos

        duration = time.time() - self.last_update
        rate = pos_diff / duration

        print("%i Pixel/sec." % rate)
        self.last_pos = pos
        self.last_update = time.time()


if __name__ == "__main__":
    width = 640
    height = 480

    canvas = Canvas(width, height)
    mandelbrot = Mandelbrot(
        canvas,
        left=-2,
        right=0.5,
        top=1.25,
        bottom=-1.25,
        iterations=40,
    )

    @js.Function
    def render_line():
        next_update = time.time() + 0.5
        while time.time()<next_update:
            mandelbrot.render_mandelbrot_line()

        if not mandelbrot.done: # not complete, yet
            mandelbrot.display_stats()

            # see: https://github.com/rfk/pypyjs/issues/117
            js.globals.setTimeout(render_line, 0)

    render_line()
