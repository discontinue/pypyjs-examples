from __future__ import absolute_import, print_function

print("imports...")

import time# after imports
import random# add comments
import math# as work-a-round
import sys# for:
from colorsys import hsv_to_rgb# https://github.com/rfk/pypyjs/issues/109

import js# from PyPy.js

CANVAS_ID="#mandelbrot"
PROGRESS_BAR_ID="#progress-bar"

class jQuery(object):
    def __init__(self):
        self.jquery = js.globals["$"]

    def get_by_id(self, id):
        dom_object = self.jquery(id)#[0]
        if dom_object == js.undefined:
            print("ERROR: Object with ID %r not found!" % id)
            sys.exit()
        return dom_object

jquery = jQuery()


class ProgressBar(object):
    def __init__(self):
        self.progress_bar = jquery.get_by_id(PROGRESS_BAR_ID)

    def set_percent(self, percent, text):
        percent = int(percent)
        self.progress_bar.attr("aria-valuenow", percent)
        self.progress_bar.width("%i%%" % percent)
        self.progress_bar.text(text)



class Canvas(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.canvas = jquery.get_by_id(CANVAS_ID)[0]
        self.context = self.canvas.getContext('2d')

        self.pixel = self.context.createImageData(1, 1)
        self.pixel_data = self.pixel.data

    def draw_rect(self, x, y, r, g, b, alpha=255, width=1, height=1):
        self.context.fillStyle = 'rgba(%i,%i,%i,%i)' % (r, g, b, alpha)
        self.context.fillRect(x, y, width, height)


class Mandelbrot(object):
    """
    FIXME: interlace rendering is not accurate, yet!
    """
    def __init__(self, canvas):
        self.canvas = canvas
        self.progress_bar = ProgressBar()

        self.width = self.canvas.width
        self.height = self.canvas.height

        self.running = True

        self.reset()

    def reset(self):
        self.progress_bar.set_percent(0, "start")
        self.y = 0
        self.step = self.height // 4
        self.line_count = 0
        self.rendered_lines = []
        self.last_update = self.start_time = time.time()
        self.last_pos = 0
        self.done = False

    def setup(self):
        self.left = float(jquery.get_by_id("#left").val())
        self.right = float(jquery.get_by_id("#right").val())
        self.top = float(jquery.get_by_id("#top").val())
        self.bottom = float(jquery.get_by_id("#bottom").val())

        print("%.1f %.1f %.1f %.1f" % (self.left, self.right, self.top, self.bottom))

        self.iterations = int(jquery.get_by_id("#iterations").val())

        # self.color_func = self.color_func_random
        # self.color_func = self.color_func_monochrome_red
        # self.color_func = self.color_func_hsv2rgb # very colorfull
        # self.color_func = self.color_func_red_green_ramp # red <-> green color ramp
        # self.color_func = self.color_func_color_steps
        # self.color_func = self.color_func_psychedelic # Psychedelic colors
        self.color_func = self.color_func_color_map # use COLOR_MAP

        self.reset()

    def color_func_monochrome_red(self, count, norm, iterations):
        return (int(256 / iterations * norm), 0, 0)

    RANDOM_MAP={}
    def color_func_random(self, count, norm, iterations):
        try:
            return self.RANDOM_MAP[count]
        except KeyError:
            self.RANDOM_MAP[count] = (r,g,b) = (random.randrange(255),random.randrange(255),random.randrange(255))
            return (r,g,b)

    def color_func_hsv2rgb(self, count, norm, iterations):
        # very colorfull ;)
        (r,g,b) = hsv_to_rgb(h=norm/iterations,s=1,v=1)
        return int(r*255), int(g*255), int(b*255)

    def color_func_red_green_ramp(self, count, norm, iterations):
        # red <-> green color ramp
        return (
            (255 * count) // iterations, # red
            (255 * (iterations - count)) // iterations, # green
            0, # blue
        )

    def color_func_color_steps(self, count, norm, iterations):
        if count <= 5:
            return (0, (255 // 5) * count, 0) # monochrome green
        elif count <= 8:
            return (0, 255, 0) # green
        elif count <= 10:
            return (0, 0, 255) # blue
        elif count <= 12:
            return (255, 0, 0) # red
        elif count <= 15:
            return (255, 255, 0) # yellow
        else:
            return (0, 0, 0) # black
    
    def color_func_psychedelic(self, count, norm, iterations):
        # Psychedelic colors:
        color = int((65536.0 / iterations) * count)
        return (
            (color >> 16) & 0xFF, # red
            (color >> 8) & 0xFF, # green
            color & 0xFF, # blue
        )

    COLOR_MAP = {
        0: (66, 30, 15),
        1: (25, 7, 26),
        2: (9, 1, 47),
        3: (4, 4, 73),
        4: (0, 7, 100),
        5: (12, 44, 138),
        6: (24, 82, 177),
        7: (57, 125, 209),
        8: (134, 181, 229),
        9: (211, 236, 248),
        10: (241, 233, 191),
        11: (248, 201, 95),
        12: (255, 170, 0),
        13: (204, 128, 0),
        14: (153, 87, 0),
        15: (106, 52, 3),
        16: (90, 40, 0),
        17: (40, 20, 0),
        18: (20, 10, 0),
        19: (10, 5, 0),
        20: (5, 0, 0),
    }
    def color_func_color_map(self, count, norm, iterations):
        try:
            return self.COLOR_MAP[count]
        except KeyError:
            if count <= 33:
                return (count * 7, count * 5, 0)
            else:
                return (0, 0, 0) # black

    def _render_line(self, canvas, color_func, y, left, right, top, bottom, width, height, iterations, rect_height):
        for x in range(width):
            z = complex(0, 0)
            c = complex(
                left + x * (right - left) / width,
                top + y * (bottom - top) / height
            )
            norm = abs(z) ** 2
            for count in xrange(iterations):
                if norm <= 4:
                    z = z * z + c
                    norm = abs(z * z)
                else:
                    break

            (r,g,b)=color_func(count, norm, iterations)
            canvas.draw_rect(x, y, r, g, b, height=rect_height)

    def render_mandelbrot(self):
        if not self.running or self.done:
            return

        rect_height = 1
        # rect_height = self.step # FIXME
        next_return = time.time() + 0.5
        while time.time() < next_return:
            if self.y >= self.height:
                if self.step <= 1:
                    self.done = True
                    duration = time.time() - self.start_time
                    self.display_stats() # Should display 100% ;)
                    print(len(self.rendered_lines), "lines are rendered")
                    msg = "%ix%ipx Rendered in %iSec." % (self.width, self.height, duration)
                    print(msg)
                    print(" --- END --- ")
                    return

                # canvas.draw_rect(x=0, y=0, r=128, g=0, b=0, alpha=128, width=self.step, height=self.height) # debug
                self.step = int(math.floor(self.step / 2.0))
                # rect_height = self.step # FIXME
                self.y = 0
                print("Render step: %i" % self.step)

            if self.y not in self.rendered_lines:
                self._render_line(
                    self.canvas,
                    self.color_func,
                    self.y,
                    self.left, self.right, self.top, self.bottom,
                    self.width, self.height, self.iterations,
                    rect_height
                )
                self.line_count += 1
                self.rendered_lines.append(self.y)

            self.y += self.step

        self.display_stats()

    def display_stats(self):
        pos = (self.line_count * self.width)
        pos_diff = pos - self.last_pos
        self.last_pos = pos

        duration = time.time() - self.last_update
        self.last_update = time.time()

        rate = pos_diff / duration
        percent = 100.0 * self.line_count / self.height
        self.progress_bar.set_percent(percent, "%.1f%% (%i Pixel/sec.)" % (percent, rate))






if __name__ == "__main__":
    print("startup rendering...")
    width = 768
    height = 432

    # width = 320
    # height = 200

    canvas = Canvas(width, height)
    mandelbrot = Mandelbrot(canvas)
    mandelbrot.setup()

    jquery.jquery("h1").append(" - " + mandelbrot.color_func.__name__)

    @js.Function
    def pause_mandelbrot(event):
        if mandelbrot.running:
            mandelbrot.running = False
            jquery.get_by_id("#pause").text("resume")
            print("pause")
        else:
            mandelbrot.running = True
            jquery.get_by_id("#pause").text("pause")
            print("resume")

    pause_button = jquery.get_by_id("#pause")
    pause_button.click(pause_mandelbrot)


    @js.Function
    def update_mandelbrot(event):
        print("update...")
        mandelbrot.running = False
        mandelbrot.setup()
        mandelbrot.running = True
        render_mandelbrot()

    update_button = jquery.get_by_id("#update")
    update_button.click(update_mandelbrot)

    @js.Function
    def render_mandelbrot():
        mandelbrot.render_mandelbrot()

        if not mandelbrot.done: # not complete, yet
            # see: https://github.com/rfk/pypyjs/issues/117
            js.globals.setTimeout(render_mandelbrot, 0)
        else:
            print("done.")

    render_mandelbrot()
