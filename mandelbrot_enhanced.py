from __future__ import absolute_import, print_function

import time# after imports
import random# add comments
import sys# for:
from colorsys import hsv_to_rgb# https://github.com/rfk/pypyjs/issues/109

import js# from PyPy.js


PY2 = sys.version_info[0] == 2
if PY2:
    # Python 2
    range = xrange


CANVAS_ID="#mandelbrot"
PROGRESS_BAR_ID="#progress-bar"


class jQuery(object):
    def __init__(self):
        self.jquery = js.globals["$"]

    def get_by_id(self, id):
        assert id.startswith("#")
        dom_object = self.jquery(id)
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

        self.reset()
        # self.pixel = self.context.createImageData(1, 1)
        # self.pixel_data = self.pixel.data

    def draw_rect(self, x, y, r, g, b, alpha=255, width=1, height=1):
        self.context.fillStyle = 'rgba(%i,%i,%i,%i)' % (r, g, b, alpha)
        self.context.fillRect(x, y, width, height)

    def reset(self):
        self.canvas = jquery.get_by_id(CANVAS_ID)[0]
        self.canvas.width = self.width
        self.canvas.height = self.height
        self.context = self.canvas.getContext('2d')


def interlace_generator(limit):
    def gen_pow(limit):
        interlace_steps = []
        step=0
        while True:
            value = 2**step
            if value>=limit:
                return interlace_steps
            interlace_steps.append(value)
            step+=1
    interlace_steps = gen_pow(limit)
    interlace_steps.reverse()
    #~ print("interlace_steps:", interlace_steps)

    pos = 0
    step = 1
    iteration = 0
    size = interlace_steps[iteration]

    while True:
        yield (pos, size)
        pos += (size * step)

        if pos>limit:
            step = 2
            iteration += 1
            try:
                size = interlace_steps[iteration]
            except IndexError:
                return

            pos = size



class Mandelbrot(object):
    LEFT = -2.0
    RIGHT = 2.0
    TOP = 2.0
    BOTTOM = -2.0

    def __init__(self, canvas):
        self.canvas = canvas
        self.progress_bar = ProgressBar()

        self.width = self.canvas.width
        self.height = self.canvas.height

        self.set_timeout_ids=[]
        self.running = True

        self.center()
        self.reset()
        self.calc_dimensions()

    def center(self):
        self.horizontal_offset = 0
        self.vertical_offset = 0
        self.zoom = 1.0
        self.running = True

    def reset(self):
        self.canvas.reset()
        self.progress_bar.set_percent(0, "start")
        self.y = 0
        self.step = self.height // 4
        self.line_count = 0
        self.last_update = self.start_time = time.time()
        self.last_pos = 0

    def calc_dimensions(self):
        print("horizontal offset..:", self.horizontal_offset)
        print("vertical offset....:", self.vertical_offset)
        print("zoom...............: x%.1f (%f)" % (1/self.zoom, self.zoom))
        self.left=(self.LEFT + self.horizontal_offset) * self.zoom
        self.right=(self.RIGHT + self.horizontal_offset) * self.zoom
        self.top=(self.TOP + self.vertical_offset) * self.zoom
        self.bottom=(self.BOTTOM + self.vertical_offset) * self.zoom
        print("Dimensions:", self.left, self.right, self.top, self.bottom)

        self.iterations = int(jquery.get_by_id("#iterations").val())
        print("Iterations:", self.iterations)

        _interlace_generator = interlace_generator(self.height)
        try:
            self.interlace_generator_next = _interlace_generator.next # Python 2
        except AttributeError:
            self.interlace_generator_next = _interlace_generator.__next__ # Python 3
        self.done = False

        # self.color_func = self.color_func_random
        # self.color_func = self.color_func_monochrome_red
        # self.color_func = self.color_func_hsv2rgb # very colorfull
        # self.color_func = self.color_func_red_green_ramp # red <-> green color ramp
        # self.color_func = self.color_func_color_steps
        # self.color_func = self.color_func_psychedelic # Psychedelic colors
        self.color_func = self.color_func_color_map # use COLOR_MAP

        self.reset()

    def stop(self):
        self.running = False
        print("stop")
        for id in self.set_timeout_ids:
            js.globals.clearTimeout(id)
        print("cleared timeouts:", self.set_timeout_ids)
        self.set_timeout_ids=[]

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
        count=0
        for x in range(width):
            z = complex(0, 0)
            c = complex(
                left + x * (right - left) / width,
                top + y * (bottom - top) / height
            )
            norm = abs(z) ** 2
            for count in range(iterations):
                if norm <= 4:
                    z = z * z + c
                    norm = abs(z * z)
                else:
                    break

            (r,g,b)=color_func(count, norm, iterations)
            canvas.draw_rect(x, y, r, g, b, height=rect_height)

    def render_mandelbrot(self):
        if not self.running or self.done:
            return self.stop()

        next_return = time.time() + 0.5
        while time.time() < next_return:
            try:
                y, size = self.interlace_generator_next()
            except StopIteration:
                self.done = True
                duration = time.time() - self.start_time
                self.display_stats() # Should display 100% ;)
                msg = "%ix%ipx Rendered in %iSec." % (self.width, self.height, duration)
                print(msg)
                print(" --- END --- ")
                return self.stop()

            self._render_line(
                self.canvas,
                self.color_func,
                y,
                self.left, self.right, self.top, self.bottom,
                self.width, self.height, self.iterations,
                rect_height=size
            )
            self.line_count += 1

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


CHANGE_SCALE = 0.5


if __name__ == "__main__":
    print("startup rendering...")
    width = height = 400

    canvas = Canvas(width, height)
    mandelbrot = Mandelbrot(canvas)

    @js.Function
    def pause_mandelbrot(event):
        if mandelbrot.running:
            print("pause")
            mandelbrot.stop()
            jquery.get_by_id("#pause").text("resume")
        else:
            print("resume")
            jquery.get_by_id("#pause").text("pause")
            mandelbrot.running = True
            render_mandelbrot()

    pause_button = jquery.get_by_id("#pause")
    pause_button.click(pause_mandelbrot)


    @js.Function
    def update_mandelbrot(event):
        print("update...")
        mandelbrot.stop()
        mandelbrot.calc_dimensions()
        mandelbrot.running = True
        render_mandelbrot()

    update_button = jquery.get_by_id("#update")
    update_button.click(update_mandelbrot)


    @js.Function
    def data_form_change(event):
        print("form, changed:")
        update_mandelbrot(event)

    data_form = jquery.get_by_id("#data_form")
    data_form.change(data_form_change)

    @js.Function
    def move_right(event):
        mandelbrot.stop()
        print("move right")
        print("zoom factor:", 1/mandelbrot.zoom)
        # mandelbrot.horizontal_offset += (CHANGE_SCALE * (1/mandelbrot.zoom))
        # if mandelbrot.horizontal_offset == 0:
        mandelbrot.horizontal_offset += CHANGE_SCALE
        # else:
        #     mandelbrot.horizontal_offset += mandelbrot.horizontal_offset * CHANGE_SCALE
        update_mandelbrot(event)
    jquery.get_by_id("#move_right").click(move_right)

    @js.Function
    def move_left(event):
        mandelbrot.stop()
        print("move left")
        # mandelbrot.horizontal_offset -= (CHANGE_SCALE * (1/mandelbrot.zoom))
        # if mandelbrot.horizontal_offset == 0:
        mandelbrot.horizontal_offset -= CHANGE_SCALE
        # else:
        #     mandelbrot.horizontal_offset -= mandelbrot.horizontal_offset * CHANGE_SCALE
        update_mandelbrot(event)
    jquery.get_by_id("#move_left").click(move_left)


    @js.Function
    def move_top(event):
        mandelbrot.stop()
        print("move top")
        mandelbrot.vertical_offset += CHANGE_SCALE
        update_mandelbrot(event)
    jquery.get_by_id("#move_top").click(move_top)

    @js.Function
    def move_bottom(event):
        mandelbrot.stop()
        print("move bottom")
        mandelbrot.vertical_offset -= CHANGE_SCALE
        update_mandelbrot(event)
    jquery.get_by_id("#move_bottom").click(move_bottom)
    
    @js.Function
    def zoom_in(event):
        mandelbrot.stop()
        print("zoom in")
        mandelbrot.zoom -= mandelbrot.zoom * CHANGE_SCALE
        mandelbrot.horizontal_offset += mandelbrot.horizontal_offset * CHANGE_SCALE
        mandelbrot.vertical_offset += mandelbrot.vertical_offset * CHANGE_SCALE
        update_mandelbrot(event)
    jquery.get_by_id("#zoom_in").click(zoom_in)

    @js.Function
    def zoom_out(event):
        mandelbrot.stop()
        print("zoom out")
        mandelbrot.zoom += mandelbrot.zoom * CHANGE_SCALE
        mandelbrot.horizontal_offset -= mandelbrot.horizontal_offset * CHANGE_SCALE
        mandelbrot.vertical_offset -= mandelbrot.vertical_offset * CHANGE_SCALE
        update_mandelbrot(event)
    jquery.get_by_id("#zoom_out").click(zoom_out)

    @js.Function
    def render_mandelbrot():
        mandelbrot.render_mandelbrot()

        if not mandelbrot.done: # not complete, yet
            # see: https://github.com/rfk/pypyjs/issues/117
            mandelbrot.set_timeout_ids.append(
                int(js.globals.setTimeout(render_mandelbrot, 0))
            )
        else:
            print("done.")

    render_mandelbrot()
