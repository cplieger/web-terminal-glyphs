"""Shades: the three dot dithers, the coarse checkerboards, stripes and diagonal hatches.

The dithers are the companion's, re-pitched to tile. Monaspace Neon NF draws the light shade as
138 x 155 dots on a 6 x 8 checkerboard (columns 207 apart, rows 311 apart, so eight rows overrun
the 2428-unit row and the pattern resets at every cell seam) and the medium shade as 138 x 159
dots on 8 x 14. Here the same dots and the same phase sit on `cell.x_bounds` / `cell.y_bounds`
lattices, so the pitch across a cell seam equals the pitch inside the cell, and the dark shade
is the full block with the light shade's dots as holes.
"""

from typing import NamedTuple

from glyphs import cell
from glyphs.contour import Contour, clip, half_plane, polygon, rect
from glyphs.families import grid, triangles


class Dither(NamedTuple):
    cols: int
    rows: int
    dot: tuple[int, int]
    phase: int  # a dot sits at (row r from the bottom, column c) iff (r + c) % 2 == phase


LIGHT = Dither(6, 8, (138, 155), 1)
MEDIUM = Dither(8, 14, (138, 159), 0)
INVERSE = MEDIUM._replace(phase=1)
KINDS = {'light': LIGHT, 'medium': MEDIUM, 'inverse': INVERSE}
# Half of the MEDIUM lattice per side, as (rows from the bottom, columns).
HALVES = {
    'n': (range(7, 14), range(8)),
    's': (range(7), range(8)),
    'w': (range(14), range(4)),
    'e': (range(14), range(4, 8)),
}
OPPOSITE = {'n': 's', 's': 'n', 'e': 'w', 'w': 'e'}
DIAGONAL_CORNERS = {
    'nw': ((0, 0), (1, 1), 1),
    'se': ((0, 0), (1, 1), -1),
    'ne': ((0, 1), (1, 0), -1),
    'sw': ((0, 1), (1, 0), 1),
}


def dots(kind: Dither, rows: range, cols: range) -> list[Contour]:
    """The dots of `kind` in the given rows (from the bottom) and columns, each centred in its
    lattice cell."""
    xs, ys = cell.x_bounds(kind.cols), cell.y_bounds(kind.rows)
    w, h = kind.dot
    out: list[Contour] = []
    for r in rows:
        for c in cols:
            if (r + c) % 2 != kind.phase:
                continue
            x0 = xs[c] + (xs[c + 1] - xs[c] - w) // 2
            y0 = ys[r] + (ys[r + 1] - ys[r] - h) // 2
            out.append(rect(x0, x0 + w, y0, y0 + h))
    return out


def dark() -> list[Contour]:
    """The full block with the light shade's dots punched out."""
    block = rect(*cell.overhang(0, cell.ADVANCE_UNITS, cell.BOTTOM_UNITS, cell.LATTICE_TOP_UNITS))
    holes = [polygon(dot, hole=True) for dot in dots(LIGHT, range(LIGHT.rows), range(LIGHT.cols))]
    return [block, *holes]


def dither(kind: str, half: str | None = None, *, fill_rest: bool = False) -> list[Contour]:
    if kind == 'dark':
        return dark()
    lattice = KINDS[kind]
    rows, cols = HALVES[half] if half else (range(lattice.rows), range(lattice.cols))
    out = dots(lattice, rows, cols)
    if fill_rest:
        rows, cols = HALVES[OPPOSITE[half]]
        xs, ys = cell.x_bounds(lattice.cols), cell.y_bounds(lattice.rows)
        out += grid.block(xs[cols[0]], xs[cols[-1] + 1], ys[rows[0]], ys[rows[-1] + 1])
    return out


def triangular(corner: str) -> list[Contour]:
    """The medium shade clipped to the half of the cell on `corner`'s side of the diagonal."""
    p, q, side = DIAGONAL_CORNERS[corner]
    plane = half_plane(triangles.at(*p), triangles.at(*q), side)
    out: list[Contour] = []
    for dot in dots(MEDIUM, range(MEDIUM.rows), range(MEDIUM.cols)):
        piece = polygon(clip(dot, *plane))
        if piece:
            out.append(piece)
    return out


def checker(*, inverse: bool) -> list[Contour]:
    return grid.cells(4, 4, {(r, c) for r in range(4) for c in range(4) if (r + c) % 2 == inverse})


def stripes() -> list[Contour]:
    return grid.cells(1, 4, {(1, 0), (3, 0)}, solid=True)


def hatch(direction: str) -> list[Contour]:
    """Four light lines per cell parallel to the cell diagonal, so the pattern continues across
    both cell edges; `direction` is 'nw-se' or 'ne-sw'."""
    w, h = cell.ADVANCE_UNITS, cell.LATTICE_HEIGHT_UNITS
    dx = w if direction == 'nw-se' else -w
    length = (dx * dx + h * h) ** 0.5
    nx, ny = h / length * cell.LIGHT_STROKE_UNITS / 2, dx / length * cell.LIGHT_STROKE_UNITS / 2
    frame = [
        half_plane(triangles.at(*p), triangles.at(*q), 1)
        for p, q in (((0, 0), (1, 0)), ((1, 0), (1, 1)), ((1, 1), (0, 1)), ((0, 1), (0, 0)))
    ]
    out: list[Contour] = []
    for x_top in cell.x_bounds(4)[:4]:
        for wrap in (0, -dx):
            x0, y0 = x_top + wrap, cell.LATTICE_TOP_UNITS
            band = [
                (x0 - 2 * dx + nx, y0 + 2 * h + ny),
                (x0 - 2 * dx - nx, y0 + 2 * h - ny),
                (x0 + 2 * dx - nx, y0 - 2 * h - ny),
                (x0 + 2 * dx + nx, y0 - 2 * h + ny),
            ]
            for plane in frame:
                band = clip(band, *plane)
            piece = polygon(band)
            if piece:
                out.append(piece)
    return out


def draw(params: dict) -> list[Contour]:
    shape = params['shape']
    if shape == 'dither':
        return dither(params['kind'], params.get('half'), fill_rest=params.get('fill_rest', False))
    if shape == 'triangular':
        return triangular(params['corner'])
    if shape == 'checker':
        return checker(inverse=params['inverse'])
    if shape == 'stripes':
        return stripes()
    if shape == 'hatch':
        return hatch(params['direction'])
    raise ValueError(shape)
