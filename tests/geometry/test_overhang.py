"""Solid glyphs exceed every cell edge they touch by exactly 72 units and stop exactly at an
internal boundary; the cell is x [0, 1240], y [-500, 1929], its stroke midline the companion's
y 645 and its lattice centre y 714."""

import pytest

OVERHANG = 72
LEFT, RIGHT = 0 - OVERHANG, 1240 + OVERHANG
BOTTOM, TOP = -500 - OVERHANG, 1929 + OVERHANG
MIDLINE = 645
CENTRE = 714
LIGHT = 160


def test_full_block_overhangs_all_four_edges(bounds):
    assert bounds(0x2588) == (LEFT, BOTTOM, RIGHT, TOP)


def test_vertical_stroke_overhangs_top_and_bottom(bounds):
    x0, y0, x1, y1 = bounds(0x2502)
    assert (y0, y1) == (BOTTOM, TOP)
    assert (x1 - x0, (x0 + x1) / 2) == (LIGHT, 620)


def test_horizontal_stroke_overhangs_left_and_right(contour_boxes):
    """The through arm of the cross, the horizontal the companion's own `─` has to meet."""
    x0, y0, x1, y1 = contour_boxes(0x253C)[0]
    assert (x0, x1) == (LEFT, RIGHT)
    assert (y1 - y0, (y0 + y1) / 2) == (LIGHT, MIDLINE)


def test_upper_half_block_overhangs_the_top_only(bounds):
    assert bounds(0x2580) == (LEFT, CENTRE, RIGHT, TOP)


@pytest.mark.parametrize(
    ('codepoint', 'expected'),
    [(0x2598, (LEFT, CENTRE, 620, TOP)), (0x259D, (620, CENTRE, RIGHT, TOP))],
    ids=['upper-left', 'upper-right'],
)
def test_upper_quadrants_overhang_their_outer_edges_only(bounds, codepoint, expected):
    assert bounds(codepoint) == expected


def test_powerline_arrow_overhangs_its_left_edge(bounds):
    x0, y0, x1, y1 = bounds(0xE0B0)
    assert (x0, y0, y1) == (LEFT, BOTTOM, TOP)
    assert x1 == 1240


@pytest.mark.parametrize('codepoint', [0x2580, 0x2598, 0x259D], ids=['upper-half', 'ul', 'ur'])
def test_half_block_internal_edge_is_the_lattice_centre(bounds, codepoint):
    """The half blocks meet only our own glyphs (the companion's `▄` does not tile at this cell),
    so they split the lattice evenly with the other eighths rather than on the stroke midline."""
    _, y0, _, _ = bounds(codepoint)
    assert y0 == CENTRE


def test_lower_eighths_step_evenly_through_the_half(bounds):
    tops = [bounds(cp)[3] for cp in range(0x2581, 0x2588)]
    assert tops == [-196, 107, 411, 714, 1018, 1321, 1625]
