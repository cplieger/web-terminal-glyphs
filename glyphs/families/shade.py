"""Shades: dithers on the 4 x 8 lattice, the coarse checkerboards, stripes and diagonal hatches.

The 25% dither puts one square per row in column 0, 2, 1, 3 (repeating), so it touches every cell
edge and tiles with a four-row period; 75% is its complement and 50% the checkerboard.
"""

from glyphs import cell
from glyphs.contour import Contour, clip, half_plane, polygon
from glyphs.families import grid, triangles

COLS, ROWS = 4, 8
LIGHT_COLUMN = (0, 2, 1, 3)
HALVES = {
    'n': (range(4), range(COLS)),
    's': (range(4, ROWS), range(COLS)),
    'w': (range(ROWS), range(2)),
    'e': (range(ROWS), range(2, COLS)),
}
OPPOSITE = {'n': 's', 's': 'n', 'e': 'w', 'w': 'e'}
DIAGONAL_CORNERS = {
    'nw': ((0, 0), (1, 1), 1),
    'se': ((0, 0), (1, 1), -1),
    'ne': ((0, 1), (1, 0), -1),
    'sw': ((0, 1), (1, 0), 1),
}


def _filled(kind: str, row: int, col: int) -> bool:
    """`row` counts from the top of the cell."""
    r = ROWS - 1 - row
    light = col == LIGHT_COLUMN[r % 4]
    return {
        'light': light,
        'dark': not light,
        'medium': (r + col) % 2 == 0,
        'inverse': (r + col) % 2 == 1,
    }[kind]


def dither(kind: str, half: str | None = None, *, fill_rest: bool = False) -> list[Contour]:
    rows, cols = HALVES[half] if half else (range(ROWS), range(COLS))
    mask = {(r, c) for r in rows for c in cols if _filled(kind, r, c)}
    out = grid.cells(COLS, ROWS, mask)
    if fill_rest:
        rows, cols = HALVES[OPPOSITE[half]]
        out += grid.cells(COLS, ROWS, {(r, c) for r in rows for c in cols}, solid=True)
    return out


def triangular(corner: str) -> list[Contour]:
    """The 50% dither clipped to the half of the cell on `corner`'s side of the diagonal."""
    p, q, side = DIAGONAL_CORNERS[corner]
    plane = half_plane(triangles.at(*p), triangles.at(*q), side)
    xs, ys = cell.x_bounds(COLS), cell.y_bounds(ROWS)
    out: list[Contour] = []
    for row in range(ROWS):
        for col in range(COLS):
            if not _filled('medium', row, col):
                continue
            x0, x1, y0, y1 = xs[col], xs[col + 1], ys[ROWS - 1 - row], ys[ROWS - row]
            piece = polygon(clip([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], *plane))
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
