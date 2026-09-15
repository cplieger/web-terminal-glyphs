"""hmtx: every glyph advances one cell, and a CFF glyph's left side bearing is its ink xMin (so a
glyph that overhangs the left edge has lsb -72 and a centred light stroke has 540)."""

import pytest

ADVANCE = 1240


def test_every_glyph_advances_one_cell(font):
    wrong = {
        name: advance for name, (advance, _) in font['hmtx'].metrics.items() if advance != ADVANCE
    }
    assert wrong == {}


@pytest.mark.parametrize(
    ('codepoint', 'lsb'),
    [(0x2588, -72), (0x2502, 540), (0x253C, -72), (0x2580, -72), (0x2590, 620), (0xE0B0, -72)],
    ids=['full-block', 'vertical', 'cross', 'upper-half', 'right-half', 'powerline-arrow'],
)
def test_left_side_bearing_is_the_ink_left_edge(font, cmap, codepoint, lsb):
    assert font['hmtx'].metrics[cmap[codepoint]] == (ADVANCE, lsb)


def test_notdef_is_empty_with_the_cell_advance(font):
    assert font['hmtx'].metrics['.notdef'] == (ADVANCE, 0)
