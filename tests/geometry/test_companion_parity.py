"""A kept glyph that can sit beside a companion glyph shares the companion's coordinates: the
stroke midline and widths, the double rails, the eighth columns. The half blocks are not here:
the companion's own halves do not tile at this cell, so ours meet only ours and stay on the
lattice centre (`test_overhang.py`).

MONASPACE holds the contour boxes measured on Monaspace Neon NF v1.400 (fontTools over the
Regular face), written here as literals so the pins come from the constants and this table, never
from the companion file. Monaspace's own frame is x -10..1250, y -610..1900; where its bound sits
on that frame the glyph is extended to our overhang, everything inside it must match exactly.
"""

import pytest

MONA_FRAME = {'x': {-10: -72, 1250: 1312}, 'y': {-610: -572, 1900: 2001}}
# Monaspace glyphs whose contours map one to one onto ours.
EXACT = {
    0x2502: [(540, -610, 700, 1900)],
    0x2503: [(420, -610, 820, 1900)],
    0x2551: [(380, -610, 540, 1900), (700, -610, 860, 1900)],
    0x2588: [(-10, -610, 1250, 1900)],
    0x2589: [(-10, -610, 1085, 1900)],
    0x258A: [(-10, -610, 930, 1900)],
    0x258B: [(-10, -610, 775, 1900)],
    0x258C: [(-10, -610, 620, 1900)],
    0x258D: [(-10, -610, 465, 1900)],
    0x258E: [(-10, -610, 310, 1900)],
    0x258F: [(-10, -610, 155, 1900)],
    0x2590: [(620, -610, 1250, 1900)],
}
# Monaspace merges a junction into one contour where ours keeps the arms apart, so the shared
# facts are the ink bounds and every internal coordinate its contours expose.
FRAME = {
    0x253C: [(-10, -610, 1250, 1900)],
    0x253B: [(-10, 445, 1250, 1900)],
    0x2534: [(-10, 565, 1250, 1900)],
    0x2514: [(540, 565, 1250, 1900)],
    0x2518: [(-10, 565, 700, 1900)],
    0x251C: [(540, -610, 1250, 1900)],
    0x2524: [(-10, -610, 700, 1900)],
    0x2570: [(540, 565, 1250, 1900)],
    0x256F: [(-10, 565, 700, 1900)],
    0x256A: [(-10, -610, 1250, 565), (-10, 725, 1250, 1900)],
    0x256B: [(-10, -610, 540, 1900), (700, -610, 1250, 1900)],
    0x256C: [
        (-10, -610, 540, 565),
        (-10, 725, 540, 1900),
        (700, -610, 1250, 565),
        (700, 725, 1250, 1900),
    ],
    0x2593: [(-10, -610, 1250, 1900)],
}
# Monaspace draws the top eighth ▔ at y 1740..1900 and the right eighth ▕ at x 1090..1250, each a
# 160-unit bar rather than an eighth of its cell. Neither meets a companion glyph on that
# coordinate (▔ only meets ▔, ▕ meets ▏ across a cell edge), so both stay the lattice eighth.
LATTICE_EIGHTHS = {0x2594: (-72, 1625, 1312, 2001), 0x2595: (1085, -572, 1312, 2001)}


def extend(box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return (
        MONA_FRAME['x'].get(x0, x0),
        MONA_FRAME['y'].get(y0, y0),
        MONA_FRAME['x'].get(x1, x1),
        MONA_FRAME['y'].get(y1, y1),
    )


def union(boxes):
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def internal(boxes) -> tuple[set[int], set[int]]:
    xs = {v for b in boxes for v in (b[0], b[2]) if v not in MONA_FRAME['x']}
    ys = {v for b in boxes for v in (b[1], b[3]) if v not in MONA_FRAME['y']}
    return xs, ys


@pytest.mark.parametrize(('codepoint', 'boxes'), EXACT.items(), ids=[f'{cp:04X}' for cp in EXACT])
def test_kept_glyph_contours_are_the_companions_extended_to_the_overhang(
    contour_boxes, codepoint, boxes
):
    assert contour_boxes(codepoint) == sorted(extend(b) for b in boxes)


@pytest.mark.parametrize(('codepoint', 'boxes'), FRAME.items(), ids=[f'{cp:04X}' for cp in FRAME])
def test_kept_junction_shares_the_companions_bounds_and_internal_lines(
    bounds, contour_boxes, codepoint, boxes
):
    assert bounds(codepoint) == extend(union(boxes))
    ours = contour_boxes(codepoint)
    our_xs = {v for b in ours for v in (b[0], b[2])}
    our_ys = {v for b in ours for v in (b[1], b[3])}
    xs, ys = internal(boxes)
    assert xs <= our_xs, xs - our_xs
    assert ys <= our_ys, ys - our_ys


@pytest.mark.parametrize(
    ('codepoint', 'expected'), LATTICE_EIGHTHS.items(), ids=['top-eighth', 'right-eighth']
)
def test_outer_eighths_stay_on_the_lattice(bounds, codepoint, expected):
    assert bounds(codepoint) == expected
