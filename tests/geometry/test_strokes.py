"""Pins on the built font for the stroke family: the heavy width, the double rails, the arc and
spinner radius, and the diagonal's reach. The dashes ship no glyph (the companion tiles them), so
their split is covered by the companion contract test's touch-set rather than a pin here."""

import pytest

OVERHUNG = (-72, -572, 1312, 2001)


def test_heavy_stroke_is_400_wide_and_overhangs_like_the_light_one(bounds):
    assert bounds(0x2503) == (420, -572, 820, 2001)


def test_double_stroke_is_two_light_strokes_160_apart(contour_boxes):
    assert contour_boxes(0x2551) == [(380, -572, 540, 2001), (700, -572, 860, 2001)]


def test_double_horizontal_rails_sit_astride_the_midline(contour_boxes):
    assert contour_boxes(0x256A) == [
        (-72, 405, 1312, 565),
        (-72, 725, 1312, 885),
        (540, -572, 700, 2001),
    ]


def test_arc_has_radius_620_to_the_stroke_centre(bounds, contour_boxes):
    assert bounds(0x2570) == (540, 565, 1312, 2001)
    assert contour_boxes(0x2570) == [
        (540, 565, 1240, 1265),
        (540, 1265, 700, 2001),
        (1240, 565, 1312, 725),
    ]


def test_spinner_has_radius_620_and_a_light_band(bounds):
    """The Fira spinner arcs share RADIUS and INNER with the circles the companion now draws; the
    arc U+EE09 is the lower half turn, so its band spans the diameter and reaches down one radius
    from the cell centre."""
    assert bounds(0xEE09) == (0, 94, 1240, 714)


@pytest.mark.parametrize('codepoint', [0x2571, 0x2572], ids=['rising', 'falling'])
def test_diagonal_runs_corner_to_corner_with_the_overhang(bounds, codepoint):
    assert bounds(codepoint) == OVERHUNG
