"""Pattern lattices span exactly the cell, x [0, 1240] and y [-500, 1929]; mosaic fills are solid
fractional blocks on that lattice and overhang its outer edges by 72.

Tolerances per family: the lattice pitch is 2428 units for a 2428.57-unit row while the frame top
rounds up to 1929, so a pattern may stop 1 unit short of the top. Braille dots are inset a quarter
pitch from their lattice cell (155 horizontally, 151 vertically), so the dot ink is that much
inside the cell on every side. The shade dots are the companion's 138 x 155 and 138 x 159, centred
in their lattice cells, so their bounds sit inside the cell by half the slack of a lattice cell.
"""

from itertools import pairwise

import pytest

CELL = (0, -500, 1240, 1929)
OVERHUNG = (-72, -572, 1312, 2001)
BRAILLE_ALL_DOTS = 0x28FF
OCTANT_ALL_SET = 0x1CDE5
SEXTANT_23456 = 0x1FB3B
DOT_INSET_X, DOT_INSET_Y = 155, 151
SEXTANT_PIECES = {
    0x1FB00: (-72, 1119, 620, 2001),
    0x1FB01: (620, 1119, 1312, 2001),
    0x1FB03: (-72, 309, 620, 1119),
    0x1FB07: (620, 309, 1312, 1119),
    0x1FB0F: (-72, -572, 620, 309),
    0x1FB1E: (620, -572, 1312, 309),
}
LIGHT_SHADE = (34, -426, 1205, 1854)
MEDIUM_SHADE = (8, -493, 1231, 1921)
LIGHT_DOT, MEDIUM_DOT = (138, 155), (138, 159)
LIGHT_COLUMNS = {34, 241, 447, 654, 861, 1067}
LIGHT_ROWS = {-426, -122, 181, 485, 788, 1092, 1395, 1699}
LATTICE_HEIGHT = 2428
# The eight single octant pieces (1, 2, 7 and 8 live among the quarter blocks) and the internal
# grid lines their edges land on: (codepoint, x-edge, (y-edge, y-edge)); x = 620, y = 107, 714, 1321.
OCTANT_PIECES = [
    (0x1CEA8, 620, (1321, None)),
    (0x1CEAB, 620, (1321, None)),
    (0x1CD00, 620, (714, 1321)),
    (0x1CD03, 620, (714, 1321)),
    (0x1CD09, 620, (107, 714)),
    (0x1CD18, 620, (107, 714)),
    (0x1CEA3, 620, (None, 107)),
    (0x1CEA0, 620, (None, 107)),
]


def within_tolerance(actual, expected, tolerance):
    return all(abs(a - e) <= t for a, e, t in zip(actual, expected, tolerance, strict=True))


@pytest.mark.parametrize(
    ('codepoint', 'expected'),
    [
        (0x2591, LIGHT_SHADE),
        (0x2592, MEDIUM_SHADE),
        (0x2593, OVERHUNG),
        (0x1FB95, CELL),
        (0x1FB96, CELL),
    ],
    ids=['light-shade', 'medium-shade', 'dark-shade', 'checker', 'inverse-checker'],
)
def test_pattern_lattice_bbox(bounds, codepoint, expected):
    box = bounds(codepoint)
    assert within_tolerance(box, expected, (0, 0, 0, 1)), box


@pytest.mark.parametrize(
    'codepoint', [OCTANT_ALL_SET, SEXTANT_23456], ids=['octant-all-set', 'sextant-23456']
)
def test_mosaic_fill_spans_the_overhung_cell(bounds, codepoint):
    assert bounds(codepoint) == OVERHUNG


@pytest.mark.parametrize(
    ('codepoint', 'expected'), SEXTANT_PIECES.items(), ids=[f'{cp:04X}' for cp in SEXTANT_PIECES]
)
def test_sextant_rows_are_809_810_809(bounds, codepoint, expected):
    assert bounds(codepoint) == expected


def dot_lattice(boxes):
    sizes = {(x1 - x0, y1 - y0) for x0, y0, x1, y1 in boxes}
    columns = sorted({x0 for x0, _, _, _ in boxes})
    rows = sorted({y0 for _, y0, _, _ in boxes})
    return sizes, columns, rows


def test_light_shade_is_the_companions_dots_on_a_6x8_checkerboard(contour_boxes):
    """Mutation: the companion's own ░ has rows 311 apart, so its top row sits 196 units below the
    next cell's bottom row; on the lattice the seam pitch equals the interior pitch."""
    dots = contour_boxes(0x2591)
    sizes, columns, rows = dot_lattice(dots)
    assert len(dots) == 24
    assert sizes == {LIGHT_DOT}
    assert (set(columns), set(rows)) == (LIGHT_COLUMNS, LIGHT_ROWS)
    for x0, y0, _, _ in dots:
        assert (rows.index(y0) + columns.index(x0)) % 2 == 1, (x0, y0)
    seam_pitch = rows[0] + LATTICE_HEIGHT - rows[-1]
    interior = {b - a for a, b in pairwise(rows)}
    assert seam_pitch in interior, (seam_pitch, interior)


def test_medium_shade_is_the_companions_dots_on_an_8x14_checkerboard(contour_boxes):
    dots = contour_boxes(0x2592)
    sizes, columns, rows = dot_lattice(dots)
    assert len(dots) == 56
    assert sizes == {MEDIUM_DOT}
    assert (len(columns), len(rows)) == (8, 14)
    assert columns[0] == 8
    for x0, y0, _, _ in dots:
        assert (rows.index(y0) + columns.index(x0)) % 2 == 0, (x0, y0)
    seam_pitch = rows[0] + LATTICE_HEIGHT - rows[-1]
    interior = {b - a for a, b in pairwise(rows)}
    assert seam_pitch in interior, (seam_pitch, interior)


def test_dark_shade_is_the_full_block_minus_the_light_dots(contour_boxes):
    boxes = contour_boxes(0x2593)
    assert len(boxes) == 25
    assert boxes[0] == OVERHUNG
    assert boxes[1:] == contour_boxes(0x2591)


def test_braille_dots_fill_the_cell_minus_the_dot_inset(bounds):
    expected = (DOT_INSET_X, -500 + DOT_INSET_Y, 1240 - DOT_INSET_X, 1929 - DOT_INSET_Y)
    box = bounds(BRAILLE_ALL_DOTS)
    assert within_tolerance(box, expected, (0, 0, 0, 1)), box


@pytest.mark.parametrize(
    ('codepoint', 'x_edge', 'y_edges'),
    OCTANT_PIECES,
    ids=lambda v: f'{v:04X}' if isinstance(v, int) and v > 2000 else None,
)
def test_octant_pieces_land_on_the_2x4_grid(bounds, codepoint, x_edge, y_edges):
    """Every single octant piece has its internal edges on the grid lines; its outer edges overhang."""
    x0, y0, x1, y1 = bounds(codepoint)
    assert x_edge in (x0, x1)
    assert {x0, x1} - {x_edge} <= {-72, 1312}
    low, high = y_edges
    assert (low is None and y0 == -572) or y0 == low
    assert (high is None and y1 == 2001) or y1 == high


def test_braille_dots_share_the_octant_grid(contour_boxes):
    """Each of the eight dots of U+28FF is centred on one cell of the 2 x 4 grid the octant pieces
    above land on; centres agree to the unit."""
    dots = contour_boxes(BRAILLE_ALL_DOTS)
    assert len(dots) == 8
    xs, ys = [0, 620, 1240], [-500, 107, 714, 1321, 1928]
    cell_centres = {
        ((xs[c] + xs[c + 1]) / 2, (ys[r] + ys[r + 1]) / 2) for c in range(2) for r in range(4)
    }
    dot_centres = {((x0 + x1) / 2, (y0 + y1) / 2) for x0, y0, x1, y1 in dots}
    assert len(dot_centres) == 8
    for dx, dy in dot_centres:
        assert any(abs(dx - cx) <= 1 and abs(dy - cy) <= 1 for cx, cy in cell_centres), (dx, dy)
