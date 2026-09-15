ASCENDER, DESCENDER, LINE_GAP = 1890, -400, 200
USE_TYPO_METRICS = 1 << 7


def test_hhea_carries_the_companion_metrics(font):
    hhea = font['hhea']
    assert (hhea.ascent, hhea.descent, hhea.lineGap) == (ASCENDER, DESCENDER, LINE_GAP)


def test_typo_metrics_equal_hhea(font):
    os2 = font['OS/2']
    assert (os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap) == (
        ASCENDER,
        DESCENDER,
        LINE_GAP,
    )


def test_os2_version_and_use_typo_metrics(font):
    os2 = font['OS/2']
    assert os2.version >= 4
    assert os2.fsSelection & USE_TYPO_METRICS


def test_win_metrics_contain_the_ink(font):
    os2, head = font['OS/2'], font['head']
    cff_box = font['CFF '].cff.topDictIndex[0].FontBBox
    assert os2.usWinAscent >= head.yMax
    assert os2.usWinDescent >= -head.yMin
    assert os2.usWinAscent >= cff_box[3]
    assert os2.usWinDescent >= -cff_box[1]


def test_units_per_em(font):
    assert font['head'].unitsPerEm == 2000


def test_cell_json_ratio(cell_json):
    assert abs(cell_json['cell']['ratio'] - 17 / 14) < 1e-6
    assert (cell_json['cell']['fontSize'], cell_json['cell']['lineHeight']) == (14, 17)


def test_the_font_agrees_with_the_cell_json_it_ships(cell_json, font):
    """A consumer's build gate reads cell.json and takes the BYTES on the release digest, so the
    one disagreement no consumer can see is between this font and its own document. Compare the
    built tables DIRECTLY against it rather than against this module's constants: agreement that
    only holds transitively, through a literal both sides happen to repeat, leaves the claim itself
    unasserted -- which is how companion.unitsPerEm shipped with nothing reading it."""
    companion = cell_json['companion']
    hhea, os2 = font['hhea'], font['OS/2']
    vertical = (companion['ascender'], companion['descender'], companion['lineGap'])
    assert font['head'].unitsPerEm == companion['unitsPerEm']
    assert {advance for advance, _ in font['hmtx'].metrics.values()} == {companion['advance']}
    assert (hhea.ascent, hhea.descent, hhea.lineGap) == vertical
    assert (os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap) == vertical


def test_the_drawn_frame_agrees_with_the_cell_json_it_ships(cell_json, bounds):
    """The full block is the one glyph touching all four cell edges, so its ink bounds ARE the
    frame cell.json declares, grown by the overhang it declares."""
    cell, advance = cell_json['cell'], cell_json['companion']['advance']
    over = cell['overhang']
    assert bounds(0x2588) == (-over, cell['bottom'] - over, advance + over, cell['top'] + over)


def test_cell_json_companion_matches_the_font(cell_json, font):
    companion = cell_json['companion']
    assert (companion['ascender'], companion['descender'], companion['lineGap']) == (
        ASCENDER,
        DESCENDER,
        LINE_GAP,
    )
    assert companion['advance'] == 1240
    assert cell_json['cell'] | {'ratio': None} == {
        'fontSize': 14,
        'lineHeight': 17,
        'ratio': None,
        'baseline': 13.5,
        'top': 1929,
        'bottom': -500,
        'overhang': 72,
    }
    assert cell_json['stack'] == [cell_json['family'], companion['family']]
    assert font['name'].getDebugName(1) == cell_json['family']
