"""Braille: eight square dots on the 2 x 4 octant lattice, each half its pitch and centred."""

from glyphs import cell
from glyphs.contour import Contour, rect

# Braille dot numbers 1-8 as (row from top, col); bit i of the code offset is dot i + 1.
DOT_CELL = {1: (0, 0), 2: (1, 0), 3: (2, 0), 4: (0, 1), 5: (1, 1), 6: (2, 1), 7: (3, 0), 8: (3, 1)}


def braille(dots: set[int]) -> list[Contour]:
    xs, ys = cell.x_bounds(2), cell.y_bounds(4)
    out: list[Contour] = []
    for dot in sorted(dots):
        row, col = DOT_CELL[dot]
        x0, x1 = xs[col], xs[col + 1]
        y0, y1 = ys[3 - row], ys[4 - row]
        dx, dy = (x1 - x0) // 4, (y1 - y0) // 4
        out.append(rect(x0 + dx, x1 - dx, y0 + dy, y1 - dy))
    return out


def draw(params: dict) -> list[Contour]:
    return braille(params['dots'])
