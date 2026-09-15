"""Which glyphs carry a horizontal stem hint, and what a stem may be. The companion's box-drawing
glyphs are hinted and FreeType snaps a hinted stem to the device rows, so a stroke of ours beside a
companion dash has to be hinted the same way or its arm lands half a row off (measured 0.56/0.63
over two rows against the dash's 0.26/0.99, Firefox DPR 1 zoom 1.1). The hints stop there: a stem
is a rectangle exactly a stroke wide, or a shade's dot row, never a block edge, a braille dot or
an eighth bar, and no two stems in a glyph overlap.
"""

import itertools

import pytest

from glyphs import table
from glyphs.families import shade

STROKE_HEIGHTS = {160, 400}
SHADE_DOT_HEIGHTS = {kind.dot[1] for kind in shade.KINDS.values()}
UNHINTED = [0x2581, 0x2594, 0x2588, 0x2580, 0x28FF, 0x1FB76, 0x25E2, 0xE0B0, 0x1CD00]


def stems(font, name: str) -> list[tuple[int, int]]:
    """(bottom, top) of every stem in the glyph's `hstem`, absolute."""
    charstring = font['CFF '].cff.topDictIndex[0].CharStrings[name]
    charstring.decompile()
    program = charstring.program
    if 'hstem' not in program:
        return []
    args = []
    for value in reversed(program[: program.index('hstem')]):
        if not isinstance(value, (int, float)):
            break
        args.insert(0, value)
    if len(args) % 2:
        args = args[1:]  # the advance width precedes the first stem
    out, position = [], 0
    for delta, height in zip(args[::2], args[1::2], strict=True):
        bottom = position + delta
        out.append((bottom, bottom + height))
        position = bottom + height
    return out


def test_every_stem_is_a_stroke_or_a_shade_dot_row_and_none_overlap(font, cmap):
    for cp, name in cmap.items():
        allowed = STROKE_HEIGHTS | (SHADE_DOT_HEIGHTS if table.TABLE[cp][0] == 'shade' else set())
        spans = stems(font, name)
        for (b0, t0), (b1, t1) in itertools.pairwise(spans):
            assert b1 >= t0, f'U+{cp:04X} stems {(b0, t0)} and {(b1, t1)} overlap'
        for bottom, top in spans:
            assert top - bottom in allowed, f'U+{cp:04X} stem {(bottom, top)} is not a stroke'


@pytest.mark.parametrize(
    ('codepoint', 'expected'),
    [
        (0x2500, [(565, 725)]),
        (0x2501, [(445, 845)]),
        (0x253C, [(565, 725)]),
        (0x253D, [(445, 845)]),  # heavy left arm contains the light right arm: one stem
        (0x256A, [(405, 565), (725, 885)]),
        (0x2591, [(y0, y0 + 155) for y0 in (-426, -122, 181, 485, 788, 1092, 1395, 1699)]),
    ],
    ids=['light-h', 'heavy-h', 'cross', 'mixed-cross', 'double-h', 'light-shade'],
)
def test_stem_positions(font, cmap, codepoint, expected):
    assert stems(font, cmap[codepoint]) == expected


@pytest.mark.parametrize('codepoint', UNHINTED, ids=[f'{cp:04X}' for cp in UNHINTED])
def test_blocks_braille_eighths_and_shapes_carry_no_hint(font, cmap, codepoint):
    assert stems(font, cmap[codepoint]) == []
