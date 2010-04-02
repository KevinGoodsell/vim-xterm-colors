from __future__ import division

import math
import re
import subprocess

class Color(object):
    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue

    _hex_matcher = re.compile('''\#?(?P<r>[0-9A-Fa-f]{2})
                                    (?P<g>[0-9A-Fa-f]{2})
                                    (?P<b>[0-9A-Fa-f]{2})''', re.VERBOSE)

    _x_colors = None

    @classmethod
    def from_string(cls, s):
        if cls._x_colors is None:
            cls._x_colors = _get_x_rgb()

        if s.lower() in cls._x_colors:
            return cls._x_colors[s.lower()]

        m = cls._hex_matcher.match(s)
        if m is None:
            raise ValueError('Bad color string: %s' % s)
        r = int(m.group('r'), 16)
        g = int(m.group('g'), 16)
        b = int(m.group('b'), 16)

        return cls(r, g, b)

    @classmethod
    def from_xterm_color(cls, color_num):
        if color_num < 16 or color_num > 255:
            raise ValueError('Bad color number: %d' % color_num)

        if color_num < 232: # RGB
            adjusted = color_num - 16
            levels = [0x00, 0x5f, 0x87, 0xaf, 0xd7, 0xff]

            blue = adjusted % 6
            adjusted //= 6
            green = adjusted % 6
            red = adjusted // 6

            return cls(levels[red], levels[green], levels[blue])

        else: # Grays
            index = color_num - 232
            level = 8 + 10 * index

            return cls(level, level, level)

    def as_hex(self):
        return '%02X%02X%02X' % (self.red, self.green, self.blue)

    def nearest_xterm(self):
        # Brute-force search, could be better
        distances = [(color_distance(self, x), x)
                     for x in self._color_map.keys()]
        distances.sort()
        (dist, c) = distances[0]

        return self._color_map[c]

    def __hash__(self):
        return hash((self.__class__, self.red, self.green, self.blue))

    def __repr__(self):
        return '%s(0x%02x, 0x%02x, 0x%02x)' % (self.__class__.__name__,
                                               self.red, self.green, self.blue)

Color._color_map = dict([(Color.from_xterm_color(i), i)
                         for i in range(16, 256)])

def color_distance(color1, color2):
    # http://www.compuphase.com/cmetric.htm
    # This isn't exactly right because the formula is for gamma-adjusted RGB
    # values.
    rmean = (color1.red + color2.red) // 2
    r = color1.red - color2.red
    g = color1.green - color2.green
    b = color1.blue - color2.blue
    return math.sqrt(
        (((512 + rmean) * r*r) >> 8) +
        4 * g*g +
        (((767 - rmean) * b*b) >> 8)
    )

_x_rgb_matcher = re.compile(r'''
    \s*(?P<r>[0-9]+)
    \s+(?P<g>[0-9]+)
    \s+(?P<b>[0-9]+)
    \s+(?P<name>.*)\n
''', re.VERBOSE)

def _get_x_rgb():
    result = {}
    proc = subprocess.Popen(['showrgb'], stdout=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    for m in _x_rgb_matcher.finditer(stdout):
        name = m.group('name').lower()
        color = Color(int(m.group('r')),
                      int(m.group('g')),
                      int(m.group('b')))
        result[name] = color

    return result
