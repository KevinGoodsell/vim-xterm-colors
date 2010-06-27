# Copyright 2010 Kevin Goodsell
#
# This file is part of vim-xterm-colors.
#
# vim-xterm-colors is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License Version 2
# as published by the Free Software Foundation.
#
# vim-xterm-colors is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with vim-xterm-colors.  If not, see
# <http://www.gnu.org/licenses/>.

from __future__ import division

import re
import subprocess
import sys

class Color(object):
    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue

    _hex_matcher = re.compile('''\#?(?P<r>[0-9A-Fa-f]{2})
                                    (?P<g>[0-9A-Fa-f]{2})
                                    (?P<b>[0-9A-Fa-f]{2})''', re.VERBOSE)

    _color_names = None
    _nearest_cache = {} # {Color(), cterm_color_num}
    _xterm_overrides = {}

    @classmethod
    def from_string(cls, s):
        if cls._color_names is None:
            cls._color_names = _get_color_names()

        if s.lower() in cls._color_names:
            return cls._color_names[s.lower()]

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

    @classmethod
    def add_xterm_overrides(cls, overrides):
        if isinstance(overrides, dict):
            overrides = overrides.items()

        for (gui, xterm) in overrides:
            c = cls.from_string(gui)
            cls._xterm_overrides[c] = int(xterm)

    def as_hex(self):
        return '%02X%02X%02X' % (self.red, self.green, self.blue)

    def nearest_xterm(self, debug=False):
        # Check overrides
        if self in self._xterm_overrides:
            return self._xterm_overrides[self]

        # Check cache
        if self in self._nearest_cache:
            return self._nearest_cache[self]

        if debug:
            nearest = self._nearest_xterms(5)
            text = ', '.join(str(x) for (dist, x) in nearest)
            print >> sys.stderr, '%r possible matches: %s' % (self, text)
        else:
            nearest = self._nearest_xterms(1)

        (dist, xterm) = nearest[0]

        # Add to cache
        self._nearest_cache[self] = xterm
        return xterm

    def _nearest_xterms(self, count, max_grays=1):
        g_distances = [(color_distance(self, x), x)
                       for x in self._xterm_grays]
        c_distances = [(color_distance(self, x), x)
                       for x in self._xterm_colors]
        if count == 1:
            result = [min(g_distances + c_distances)]
        else:
            g_distances.sort()
            dists = c_distances + g_distances[:max_grays]
            dists.sort()
            result = dists[:count]

        return [(dist, self._color_map[c]) for (dist, c) in result]

    def _tuple(self):
        return (self.__class__, self.red, self.green, self.blue)

    def __hash__(self):
        return hash(self._tuple())

    def __eq__(self, other):
        return self._tuple() == other._tuple()

    def __repr__(self):
        return '%s(0x%02x, 0x%02x, 0x%02x)' % (self.__class__.__name__,
                                               self.red, self.green, self.blue)

# grays are distributed every (36+6+1) in the colorcube (16 to 231), and make
# up the last elements, 232 to 255.
_xterm_gray_indices = set(range(16, 232, 36+6+1) + range(232, 256))
Color._color_map = {}
Color._xterm_grays = []
Color._xterm_colors = []
for i in range(16, 256):
    c = Color.from_xterm_color(i)
    Color._color_map[c] = i
    if i in _xterm_gray_indices:
        Color._xterm_grays.append(c)
    else:
        Color._xterm_colors.append(c)

def color_distance(color1, color2):
    # http://www.compuphase.com/cmetric.htm
    # This isn't exactly right because the formula is for gamma-adjusted RGB
    # values.
    rmean = (color1.red + color2.red) // 2
    r = color1.red - color2.red
    g = color1.green - color2.green
    b = color1.blue - color2.blue
    # This should technically be a square root, but for comparison purposes
    # the squared distance is fine.
    return (
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

_extra_color_names = {
    # These colors are listed in :help gui-colors as colors that should be
    # available on most systems, but they aren't in the X rgb database (at
    # least not on mine).
    'lightred'       : Color(0xff, 0xbb, 0xbb),
    'lightmagenta'   : Color(0xff, 0xbb, 0xff),
    'darkyellow'     : Color(0xbb, 0xbb, 0x00),
}

def _get_color_names():
    result = _get_x_rgb()
    result.update(_extra_color_names)
    return result

if __name__ == '__main__':
    import math

    for color in sys.argv[1:]:
        try:
            c = Color.from_string(color)
        except ValueError:
            continue

        dists = c._nearest_xterms(8, 2)
        pieces = ['%d (%f)' % (x, math.sqrt(d)) for (d, x) in dists]
        print '%s = %r: %s' % (color, c, ', '.join(pieces))
