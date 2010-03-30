from __future__ import division

import math
import re

class Color(object):
    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue

    _hex_matcher = re.compile('''\#?(?P<r>[0-9A-Fa-f]{2})
                                    (?P<g>[0-9A-Fa-f]{2})
                                    (?P<b>[0-9A-Fa-f]{2})''', re.VERBOSE)

    @classmethod
    def from_string(cls, s):
        m = cls._hex_matcher.match(s)
        if m is None:
            raise ValueError('Bad color string: %s' % s)
        r = int(m.group('r'), 16)
        g = int(m.group('g'), 16)
        b = int(m.group('b'), 16)

        return Color(r, g, b)

    def as_hex(self):
        return '%02X%02X%02X' % (self.red, self.green, self.blue)

    def __hash__(self):
        return hash((self.__class__, self.red, self.green, self.blue))

    def __repr__(self):
        return '%s(%02x, %02x, %02x)' % (self.__class__.__name__, self.red,
                                         self.green, self.blue)

def color_distance(color1, color2):
    # http://www.compuphase.com/cmetric.htm
    rmean = (color1.red + color2.red) // 2
    r = color1.red - color2.red
    g = color1.green - color2.green
    b = color1.blue - color2.blue
    return math.sqrt(
        (((512 + rmean) * r*r) >> 8) +
        4 * g*g +
        (((767 - rmean) * b*b) >> 8)
    )

def xterm_color(color_num):
    if color_num < 16 or color_num > 255:
        raise ValueError('Bad color number: %d' % color_num)

    if color_num < 232: # RGB
        adjusted = color_num - 16
        levels = [0x00, 0x5f, 0x87, 0xaf, 0xd7, 0xff]

        blue = adjusted % 6
        adjusted //= 6
        green = adjusted % 6
        red = adjusted // 6

        return Color(levels[red], levels[green], levels[blue])

    else: # Grays
        index = color_num - 232
        level = 8 + 10 * index

        return Color(level, level, level)

_color_map = dict([(xterm_color(i), i) for i in range(16, 256)])

def nearest_xterm(color):
    # Brute-force search, could be better
    distances = [(color_distance(color, x), x) for x in _color_map.keys()]
    distances.sort()
    (dist, c) = distances[0]

    return _color_map[c]
