"""Solid glyphs exceed every cell edge they touch by exactly 72 units and stop exactly at an
internal boundary; the cell is x [0, 1240], y [-500, 1929], its midline y 714."""

import pytest

OVERHANG = 72
LEFT, RIGHT = 0 - OVERHANG, 1240 + OVERHANG
BOTTOM, TOP = -500 - OVERHANG, 1929 + OVERHANG
MIDLINE = 714
LIGHT = 160


def test_full_block_overhangs_all_four_edges(bounds):
    assert bounds(0x2588) == (LEFT, BOTTOM, RIGHT, TOP)


def test_vertical_stroke_overhangs_top_and_bottom(bounds):
    x0, y0, x1, y1 = bounds(0x2502)
    assert (y0, y1) == (BOTTOM, TOP)
    assert (x1 - x0, (x0 + x1) / 2) == (LIGHT, 620)


def test_horizontal_stroke_overhangs_left_and_right(bounds):
    x0, y0, x1, y1 = bounds(0x2500)
    assert (x0, x1) == (LEFT, RIGHT)
    assert (y1 - y0, (y0 + y1) / 2) == (LIGHT, MIDLINE)


def test_upper_half_block_overhangs_the_top_only(bounds):
    assert bounds(0x2580) == (LEFT, MIDLINE, RIGHT, TOP)


def test_lower_half_block_overhangs_the_bottom_only(bounds):
    assert bounds(0x2584) == (LEFT, BOTTOM, RIGHT, MIDLINE)


def test_powerline_arrow_overhangs_its_left_edge(bounds):
    x0, y0, x1, y1 = bounds(0xE0B0)
    assert (x0, y0, y1) == (LEFT, BOTTOM, TOP)
    assert x1 == 1240


@pytest.mark.parametrize('codepoint', [0x2580, 0x2584], ids=['upper-half', 'lower-half'])
def test_half_block_internal_edge_is_the_midline(bounds, codepoint):
    _, y0, _, y1 = bounds(codepoint)
    assert MIDLINE in (y0, y1)
