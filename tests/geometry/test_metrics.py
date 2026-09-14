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
