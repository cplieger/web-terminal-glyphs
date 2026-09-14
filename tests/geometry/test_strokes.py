"""Pins on the built font for the stroke family: the heavy width, the double gap, the 2 / 3 / 4
dash split with its equal gaps (154 horizontally, 302 vertically, half a gap at each cell edge),
the arc and circle radius, and the diagonal's reach."""

import pytest

OVERHUNG = (-72, -572, 1312, 2001)


def test_heavy_stroke_is_400_wide_and_overhangs_like_the_light_one(bounds):
    assert bounds(0x2503) == (420, -572, 820, 2001)


def test_double_stroke_is_two_light_strokes_160_apart(contour_boxes):
    assert contour_boxes(0x2550) == [(-72, 474, 1312, 634), (-72, 794, 1312, 954)]


@pytest.mark.parametrize(
    ('codepoint', 'segments'),
    [
        (0x254C, [(77, 634, 543, 794), (697, 634, 1163, 794)]),
        (0x2504, [(77, 634, 336, 794), (490, 634, 750, 794), (904, 634, 1163, 794)]),
        (
            0x2508,
            [
                (77, 634, 233, 794),
                (387, 634, 543, 794),
                (697, 634, 853, 794),
                (1007, 634, 1163, 794),
            ],
        ),
        (0x2506, [(540, -349, 700, 158), (540, 460, 700, 968), (540, 1270, 700, 1777)]),
    ],
    ids=['double-dash', 'triple-dash', 'quadruple-dash', 'vertical-triple-dash'],
)
def test_dashes_split_the_stroke_with_equal_gaps_and_no_overhang(
    contour_boxes, codepoint, segments
):
    assert contour_boxes(codepoint) == segments


def test_arc_has_radius_620_to_the_stroke_centre(bounds, contour_boxes):
    assert bounds(0x256D) == (540, -572, 1312, 794)
    assert contour_boxes(0x256D) == [
        (540, -572, 700, 94),
        (540, 94, 1240, 794),
        (1240, 634, 1312, 794),
    ]


def test_circle_has_radius_620_and_a_light_ring(contour_boxes):
    assert contour_boxes(0x25CB) == [(0, 94, 1240, 1334), (160, 254, 1080, 1174)]


@pytest.mark.parametrize('codepoint', [0x2571, 0x2572], ids=['rising', 'falling'])
def test_diagonal_runs_corner_to_corner_with_the_overhang(bounds, codepoint):
    assert bounds(codepoint) == OVERHUNG
