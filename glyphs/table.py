"""Codepoint -> (family, params) for every generated glyph, built from the Unicode names where
they encode the shape (box arms, block fractions, mosaic masks, diagonal endpoints) and
hand-listed for the PUA ranges (Powerline, Fira progress, kitty branch drawing)."""

import unicodedata
from itertools import pairwise

from glyphs import cell

Entry = tuple[str, dict]

ARMS = {'UP': 'n', 'DOWN': 's', 'LEFT': 'w', 'RIGHT': 'e', 'VERTICAL': 'ns', 'HORIZONTAL': 'ew'}
WEIGHTS = {'LIGHT': 'light', 'HEAVY': 'heavy', 'SINGLE': 1, 'DOUBLE': 2}
DASHES = {'DOUBLE': 2, 'TRIPLE': 3, 'QUADRUPLE': 4}
FRACTIONS = {
    'ONE EIGHTH': (1, 8),
    'ONE QUARTER': (2, 8),
    'THREE EIGHTHS': (3, 8),
    'HALF': (4, 8),
    'FIVE EIGHTHS': (5, 8),
    'THREE QUARTERS': (6, 8),
    'SEVEN EIGHTHS': (7, 8),
    'ONE THIRD': (1, 3),
    'TWO THIRDS': (2, 3),
}
SIDES = ('LEFT', 'RIGHT', 'UPPER', 'LOWER')
POINTS = {
    'UPPER LEFT': (0, 1),
    'UPPER CENTRE': (0.5, 1),
    'UPPER RIGHT': (1, 1),
    'UPPER MIDDLE LEFT': (0, 2 / 3),
    'UPPER MIDDLE RIGHT': (1, 2 / 3),
    'MIDDLE LEFT': (0, 0.5),
    'MIDDLE CENTRE': (0.5, 0.5),
    'MIDDLE RIGHT': (1, 0.5),
    'LOWER MIDDLE LEFT': (0, 1 / 3),
    'LOWER MIDDLE RIGHT': (1, 1 / 3),
    'LOWER LEFT': (0, 0),
    'LOWER CENTRE': (0.5, 0),
    'LOWER RIGHT': (1, 0),
}
CORNERS = {'UPPER LEFT': (0, 1), 'UPPER RIGHT': (1, 1), 'LOWER LEFT': (0, 0), 'LOWER RIGHT': (1, 0)}
FULL = ((0, 0), (1, 0), (1, 1), (0, 1))
BL, BR, TR, TL = FULL
C = (0.5, 0.5)
BRANCH_CORNER = {'tl': ('s', 'e'), 'tr': ('s', 'w'), 'bl': ('n', 'e'), 'br': ('n', 'w')}


def name(cp: int) -> str:
    return unicodedata.name(chr(cp)).removeprefix('BOX DRAWINGS ')


def box_arms(text: str) -> dict:
    """'DOWN LIGHT AND RIGHT HEAVY' -> {'s': 'light', 'e': 'heavy'}; a phrase without a weight
    takes the previous phrase's."""
    arms: dict = {}
    weight = None
    for phrase in text.split(' AND '):
        words = phrase.split()
        weight = next((WEIGHTS[w] for w in words if w in WEIGHTS), weight)
        for word in words:
            for arm in ARMS.get(word, ''):
                arms[arm] = weight
    return arms


def fraction_box(text: str) -> tuple[int, int, int, int]:
    """'RIGHT HALF LOWER ONE QUARTER' -> the lattice rectangle at those edges."""
    x0, x1, y0, y1 = 0, cell.ADVANCE_UNITS, cell.BOTTOM_UNITS, cell.LATTICE_TOP_UNITS
    words = text.removesuffix(' BLOCK').split()
    starts = [i for i, w in enumerate(words) if w in SIDES] + [len(words)]
    for a, b in pairwise(starts):
        side, num, den = words[a], *FRACTIONS[' '.join(words[a + 1 : b])]
        if side == 'LEFT':
            x1 = cell.x_bounds(den)[num]
        elif side == 'RIGHT':
            x0 = cell.x_bounds(den)[den - num]
        elif side == 'LOWER':
            y1 = cell.y_bounds(den)[num]
        else:
            y0 = cell.y_bounds(den)[den - num]
    return x0, x1, y0, y1


def mosaic_mask(text: str, cols: int) -> set[tuple[int, int]]:
    """'BLOCK OCTANT-2345678' -> {(row, col)} with Unicode's row-major piece numbers."""
    digits = text.rsplit('-', 1)[1]
    return {((int(d) - 1) // cols, (int(d) - 1) % cols) for d in digits}


def quadrant_mask(text: str) -> set[tuple[int, int]]:
    return {
        (0 if 'UPPER' in part else 1, 0 if 'LEFT' in part else 1)
        for part in text.removeprefix('QUADRANT ').split(' AND ')
    }


def polylines(text: str) -> list[list[tuple[int, int]]]:
    """'UPPER CENTRE TO MIDDLE LEFT AND MIDDLE RIGHT TO LOWER CENTRE' -> lattice polylines."""
    lines = []
    for run in text.split(' AND '):
        lines.append(
            [
                (
                    round(fx * cell.ADVANCE_UNITS),
                    round(cell.BOTTOM_UNITS + fy * cell.LATTICE_HEIGHT_UNITS),
                )
                for fx, fy in (POINTS[p] for p in run.split(' TO '))
            ]
        )
    return lines


def box_drawing(cp: int) -> Entry:
    text = name(cp)
    if 'DASH' in text:
        weight, dash, _, axis = text.split()
        return 'strokes', {
            'shape': 'dashed',
            'axis': 'v' if axis == 'VERTICAL' else 'h',
            'weight': WEIGHTS[weight],
            'dashes': DASHES[dash],
        }
    if 'ARC' in text:
        arms = box_arms(text.replace('LIGHT ARC ', ''))
        return 'round', {
            'shape': 'corners',
            'arms': [(next(a for a in arms if a in 'ns'), next(a for a in arms if a in 'ew'))],
        }
    if 'DIAGONAL CROSS' in text:
        return 'strokes', {
            'shape': 'diagonal',
            'lines': polylines('UPPER RIGHT TO LOWER LEFT')
            + polylines('UPPER LEFT TO LOWER RIGHT'),
        }
    if 'DIAGONAL' in text:
        return 'strokes', {
            'shape': 'diagonal',
            'lines': polylines(text.removeprefix('LIGHT DIAGONAL ')),
        }
    if 'SINGLE' in text or 'DOUBLE' in text:
        return 'strokes', {'shape': 'double', **box_arms(text)}
    return 'strokes', {'shape': 'box', **box_arms(text)}


def block_element(cp: int) -> Entry:
    text = name(cp)
    if text == 'FULL BLOCK':
        return 'grid', {'shape': 'blocks', 'boxes': [fraction_box('')]}
    if 'SHADE' in text:
        return 'shade', {'shape': 'dither', 'kind': text.split()[0].lower()}
    if text.startswith('QUADRANT'):
        return 'grid', {
            'shape': 'cells',
            'cols': 2,
            'rows': 2,
            'mask': quadrant_mask(text),
            'solid': True,
        }
    return 'grid', {'shape': 'blocks', 'boxes': [fraction_box(text)]}


def legacy_computing(cp: int) -> Entry:
    text = name(cp)
    if text.startswith('BLOCK SEXTANT'):
        return 'grid', {
            'shape': 'cells',
            'cols': 2,
            'rows': 3,
            'mask': mosaic_mask(text, 2),
            'solid': True,
        }
    if 'BLOCK DIAGONAL' in text:
        region, _, line = text.partition(' BLOCK DIAGONAL ')
        p, q = line.split(' TO ')
        return 'triangles', {
            'shape': 'wedge',
            'p': POINTS[p],
            'q': POINTS[q],
            'keep': CORNERS[region],
        }
    if text.startswith('VERTICAL ONE EIGHTH BLOCK-'):
        return 'grid', {'shape': 'eighths', 'cols': {int(text[-1])}}
    if text.startswith('HORIZONTAL ONE EIGHTH BLOCK-'):
        return 'grid', {'shape': 'eighths', 'rows': {int(d) for d in text.rsplit('-', 1)[1]}}
    if text.endswith('ONE EIGHTH BLOCK'):
        sides = text.removesuffix(' ONE EIGHTH BLOCK').split(' AND ')
        return 'grid', {
            'shape': 'eighths',
            'cols': {1 if s == 'LEFT' else 8 for s in sides if s in ('LEFT', 'RIGHT')},
            'rows': {1 if s == 'UPPER' else 8 for s in sides if s in ('UPPER', 'LOWER')},
        }
    if 'MEDIUM SHADE' in text:
        return 'shade', shade_params(text)
    if text.endswith('DIAGONAL DIAMOND'):
        return 'strokes', {
            'shape': 'diagonal',
            'lines': polylines(
                'UPPER CENTRE TO MIDDLE LEFT TO LOWER CENTRE TO MIDDLE RIGHT TO UPPER CENTRE'
            ),
        }
    if 'DIAGONAL' in text:
        return 'strokes', {
            'shape': 'diagonal',
            'lines': polylines(text.removeprefix('LIGHT DIAGONAL ')),
        }
    if 'JUSTIFIED' in text and 'QUARTER' in text:
        side = text.split(' JUSTIFIED')[0].split()
        return 'round', {
            'shape': 'quarter',
            'corner': ('n' if side[0] == 'TOP' else 's') + ('e' if side[1] == 'RIGHT' else 'w'),
        }
    if 'JUSTIFIED' in text:
        edge = {'TOP': 'n', 'BOTTOM': 's', 'LEFT': 'w', 'RIGHT': 'e'}[text.split()[0]]
        return 'round', {'shape': 'justified', 'edge': edge, 'outline': 'WHITE' in text}
    return 'grid', {'shape': 'blocks', 'boxes': [fraction_box(text)]}


def shade_params(text: str) -> dict:
    kind = 'inverse' if 'INVERSE' in text else 'medium'
    halves = {'UPPER HALF': 'n', 'LOWER HALF': 's', 'LEFT HALF': 'w', 'RIGHT HALF': 'e'}
    shaded = next(
        (
            h
            for phrase, h in halves.items()
            if f'{phrase} {"INVERSE " if kind == "inverse" else ""}MEDIUM SHADE' in text
        ),
        None,
    )
    return {'shape': 'dither', 'kind': kind, 'half': shaded, 'fill_rest': 'BLOCK' in text}


def supplement(cp: int) -> Entry:
    text = name(cp)
    if text.startswith('SEPARATED BLOCK QUADRANT'):
        return 'grid', {
            'shape': 'cells',
            'cols': 2,
            'rows': 2,
            'mask': mosaic_mask(text, 2),
            'inset': cell.LIGHT_STROKE_UNITS // 2,
        }
    if text.startswith('SEPARATED BLOCK SEXTANT'):
        return 'grid', {
            'shape': 'cells',
            'cols': 2,
            'rows': 3,
            'mask': mosaic_mask(text, 2),
            'inset': cell.LIGHT_STROKE_UNITS // 2,
        }
    if text.startswith('BLOCK OCTANT'):
        return 'grid', {
            'shape': 'cells',
            'cols': 2,
            'rows': 4,
            'mask': mosaic_mask(text, 2),
            'solid': True,
        }
    if text.endswith('ONE SIXTEENTH BLOCK'):
        i = cp - 0x1CE90
        return 'grid', {
            'shape': 'cells',
            'cols': 4,
            'rows': 4,
            'mask': {(i // 4, i % 4)},
            'solid': True,
        }
    if text.endswith('CIRCLE'):
        n = 2 if 'QUARTER' in text else 4
        return 'round', {
            'shape': 'grid_arc',
            'n': n,
            **CIRCLE_GRID[text.removesuffix(' TWELFTH CIRCLE').removesuffix(' QUARTER CIRCLE')],
        }
    if 'DOUBLE DIAGONAL' in text:
        (p, q), *_ = polylines(text.removeprefix('DOUBLE DIAGONAL '))
        return 'strokes', {'shape': 'double_diagonal', 'p': p, 'q': q}
    return 'grid', {'shape': 'blocks', 'boxes': [fraction_box(text)]}


CIRCLE_GRID = {
    'UPPER LEFT': {'col': 0, 'row': 0},
    'UPPER CENTRE LEFT': {'col': 1, 'row': 0},
    'UPPER CENTRE RIGHT': {'col': 2, 'row': 0},
    'UPPER RIGHT': {'col': 3, 'row': 0},
    'UPPER MIDDLE LEFT': {'col': 0, 'row': 1},
    'UPPER MIDDLE RIGHT': {'col': 3, 'row': 1},
    'LOWER MIDDLE LEFT': {'col': 0, 'row': 2},
    'LOWER MIDDLE RIGHT': {'col': 3, 'row': 2},
    'LOWER LEFT': {'col': 0, 'row': 3},
    'LOWER CENTRE LEFT': {'col': 1, 'row': 3},
    'LOWER CENTRE RIGHT': {'col': 2, 'row': 3},
    'LOWER RIGHT': {'col': 3, 'row': 3},
}
QUARTER_GRID = {0x1CC35: (0, 0), 0x1CC36: (1, 0), 0x1CC39: (0, 1), 0x1CC3A: (1, 1)}

XS4, YS4 = cell.x_bounds(4), cell.y_bounds(4)
X_STUB = XS4[3]
Y_LOW, Y_HIGH = YS4[1], YS4[3]
H = cell.LIGHT_STROKE_UNITS // 2
STUBS = {
    0x1CC1B: [
        (0, cell.ADVANCE_UNITS, cell.MIDLINE_Y - H, cell.MIDLINE_Y + H),
        (X_STUB - H, X_STUB + H, cell.MIDLINE_Y, cell.LATTICE_TOP_UNITS),
    ],
    0x1CC1C: [
        (0, cell.ADVANCE_UNITS, cell.MIDLINE_Y - H, cell.MIDLINE_Y + H),
        (X_STUB - H, X_STUB + H, cell.BOTTOM_UNITS, cell.MIDLINE_Y),
    ],
    0x1CC1D: [
        (cell.CENTRE_X - H, cell.CENTRE_X + H, Y_HIGH - H, cell.LATTICE_TOP_UNITS),
        (0, cell.CENTRE_X + H, Y_HIGH - H, Y_HIGH + H),
    ],
    0x1CC1E: [
        (cell.CENTRE_X - H, cell.CENTRE_X + H, cell.BOTTOM_UNITS, Y_LOW + H),
        (0, cell.CENTRE_X + H, Y_LOW - H, Y_LOW + H),
    ],
    0x1CE16: [
        (cell.CENTRE_X - H, cell.CENTRE_X + H, cell.BOTTOM_UNITS, cell.LATTICE_TOP_UNITS),
        (cell.CENTRE_X, cell.ADVANCE_UNITS, Y_HIGH - H, Y_HIGH + H),
    ],
    0x1CE17: [
        (cell.CENTRE_X - H, cell.CENTRE_X + H, cell.BOTTOM_UNITS, cell.LATTICE_TOP_UNITS),
        (cell.CENTRE_X, cell.ADVANCE_UNITS, Y_LOW - H, Y_LOW + H),
    ],
    0x1CE18: [
        (cell.CENTRE_X - H, cell.CENTRE_X + H, cell.BOTTOM_UNITS, cell.LATTICE_TOP_UNITS),
        (0, cell.CENTRE_X, Y_HIGH - H, Y_HIGH + H),
    ],
    0x1CE19: [
        (cell.CENTRE_X - H, cell.CENTRE_X + H, cell.BOTTOM_UNITS, cell.LATTICE_TOP_UNITS),
        (0, cell.CENTRE_X, Y_LOW - H, Y_LOW + H),
    ],
}
QUARTER_BLOCKS = {
    0x1FBE4: (XS4[1], XS4[3], cell.MIDLINE_Y, cell.LATTICE_TOP_UNITS),
    0x1FBE5: (XS4[1], XS4[3], cell.BOTTOM_UNITS, cell.MIDLINE_Y),
    0x1FBE6: (0, cell.CENTRE_X, Y_LOW, Y_HIGH),
    0x1FBE7: (cell.CENTRE_X, cell.ADVANCE_UNITS, Y_LOW, Y_HIGH),
}
TRIANGULAR_BLOCKS = {
    0x1FB68: [[BL, BR, TR, TL, C]],
    0x1FB69: [[TL, C, TR, BR, BL]],
    0x1FB6A: [[TL, TR, C, BR, BL]],
    0x1FB6B: [[TL, TR, BR, C, BL]],
    0x1FB6C: [[BL, C, TL]],
    0x1FB6D: [[TL, C, TR]],
    0x1FB6E: [[TR, C, BR]],
    0x1FB6F: [[BR, C, BL]],
    0x1FB9A: [[TL, C, TR], [BR, C, BL]],
    0x1FB9B: [[BL, C, TL], [TR, C, BR]],
}
GEOMETRIC = {
    0x25C9: ('round', {'shape': 'circle', 'kind': 'fisheye'}),
    0x25CB: ('round', {'shape': 'circle', 'kind': 'white'}),
    0x25CF: ('round', {'shape': 'circle', 'kind': 'black'}),
    0x25D6: ('round', {'shape': 'half_disc', 'bulge': 'w'}),
    0x25D7: ('round', {'shape': 'half_disc', 'bulge': 'e'}),
    0x25DC: ('round', {'shape': 'spinner', 'a0': 90, 'a1': 180}),
    0x25DD: ('round', {'shape': 'spinner', 'a0': 0, 'a1': 90}),
    0x25DE: ('round', {'shape': 'spinner', 'a0': 270, 'a1': 360}),
    0x25DF: ('round', {'shape': 'spinner', 'a0': 180, 'a1': 270}),
    0x25E0: ('round', {'shape': 'spinner', 'a0': 0, 'a1': 180}),
    0x25E1: ('round', {'shape': 'spinner', 'a0': 180, 'a1': 360}),
    0x25E2: ('triangles', {'shape': 'poly', 'shapes': [[BL, BR, TR]]}),
    0x25E3: ('triangles', {'shape': 'poly', 'shapes': [[BL, BR, TL]]}),
    0x25E4: ('triangles', {'shape': 'poly', 'shapes': [[BL, TR, TL]]}),
    0x25E5: ('triangles', {'shape': 'poly', 'shapes': [[TL, BR, TR]]}),
}
CHEVRON_E = polylines('UPPER LEFT TO MIDDLE RIGHT TO LOWER LEFT')
CHEVRON_W = polylines('UPPER RIGHT TO MIDDLE LEFT TO LOWER RIGHT')
BACKSLASH = polylines('UPPER LEFT TO LOWER RIGHT')
SLASH = polylines('UPPER RIGHT TO LOWER LEFT')
POWERLINE = {
    0xE0B0: ('triangles', {'shape': 'arrow', 'direction': 'e'}),
    0xE0B1: ('strokes', {'shape': 'diagonal', 'lines': CHEVRON_E}),
    0xE0B2: ('triangles', {'shape': 'arrow', 'direction': 'w'}),
    0xE0B3: ('strokes', {'shape': 'diagonal', 'lines': CHEVRON_W}),
    0xE0B4: ('round', {'shape': 'half_disc', 'bulge': 'e'}),
    0xE0B5: ('round', {'shape': 'half_disc', 'bulge': 'e', 'outline': True}),
    0xE0B6: ('round', {'shape': 'half_disc', 'bulge': 'w'}),
    0xE0B7: ('round', {'shape': 'half_disc', 'bulge': 'w', 'outline': True}),
    0xE0B8: GEOMETRIC[0x25E3],
    0xE0B9: ('strokes', {'shape': 'diagonal', 'lines': BACKSLASH}),
    0xE0BA: GEOMETRIC[0x25E2],
    0xE0BB: ('strokes', {'shape': 'diagonal', 'lines': SLASH}),
    0xE0BC: GEOMETRIC[0x25E4],
    0xE0BD: ('strokes', {'shape': 'diagonal', 'lines': SLASH}),
    0xE0BE: GEOMETRIC[0x25E5],
    0xE0BF: ('strokes', {'shape': 'diagonal', 'lines': BACKSLASH}),
    0xE0D6: ('triangles', {'shape': 'arrow', 'direction': 'w', 'inverted': True}),
    0xE0D7: ('triangles', {'shape': 'arrow', 'direction': 'e', 'inverted': True}),
}
# Fira Code progress: three capsule parts empty then filled, then six spinner arcs given here in
# kitty's y-down degrees, negated below.
PROGRESS_PARTS = ('w', 'm', 'e')
SPINNER_ARCS = ((235, 305), (270, 390), (315, 470), (360, 540), (80, 220), (170, 270))
COMMIT_LINES = (
    '',
    'e',
    'w',
    'we',
    's',
    'n',
    'sn',
    'es',
    'ws',
    'en',
    'wn',
    'nse',
    'nsw',
    'wes',
    'wen',
    'wens',
)
BRANCH = {
    0xF5D0: ('strokes', {'shape': 'box', 'e': 'light', 'w': 'light'}),
    0xF5D1: ('strokes', {'shape': 'box', 'n': 'light', 's': 'light'}),
    0xF5D2: ('strokes', {'shape': 'fading', 'axis': 'h', 'count': 4, 'toward': 'e'}),
    0xF5D3: ('strokes', {'shape': 'fading', 'axis': 'h', 'count': 4, 'toward': 'w'}),
    0xF5D4: ('strokes', {'shape': 'fading', 'axis': 'v', 'count': 5, 'toward': 's'}),
    0xF5D5: ('strokes', {'shape': 'fading', 'axis': 'v', 'count': 5, 'toward': 'n'}),
}
BRANCH_CORNERS = {
    0xF5D6: ('tl',),
    0xF5D7: ('tr',),
    0xF5D8: ('bl',),
    0xF5D9: ('br',),
    0xF5DA: ('v', 'bl'),
    0xF5DB: ('v', 'tl'),
    0xF5DC: ('bl', 'tl'),
    0xF5DD: ('v', 'br'),
    0xF5DE: ('v', 'tr'),
    0xF5DF: ('tr', 'br'),
    0xF5E0: ('h', 'tr'),
    0xF5E1: ('h', 'tl'),
    0xF5E2: ('tl', 'tr'),
    0xF5E3: ('h', 'br'),
    0xF5E4: ('h', 'bl'),
    0xF5E5: ('bl', 'br'),
    0xF5E6: ('v', 'bl', 'br'),
    0xF5E7: ('v', 'tl', 'tr'),
    0xF5E8: ('h', 'tr', 'br'),
    0xF5E9: ('h', 'bl', 'tl'),
    0xF5EA: ('v', 'tl', 'br'),
    0xF5EB: ('v', 'tr', 'bl'),
    0xF5EC: ('h', 'tl', 'br'),
    0xF5ED: ('h', 'tr', 'bl'),
}


def build() -> dict[int, Entry]:
    table: dict[int, Entry] = {}
    for cp in range(0x2500, 0x2580):
        table[cp] = box_drawing(cp)
    for cp in range(0x2580, 0x25A0):
        table[cp] = block_element(cp)
    table.update(GEOMETRIC)
    for cp in range(0x2800, 0x2900):
        table[cp] = ('dots', {'dots': {i + 1 for i in range(8) if (cp - 0x2800) >> i & 1}})
    table.update(POWERLINE)
    for i in range(6):
        table[0xEE00 + i] = (
            'round',
            {'shape': 'progress', 'part': PROGRESS_PARTS[i % 3], 'filled': i >= 3},
        )
    for i, (a0, a1) in enumerate(SPINNER_ARCS):
        table[0xEE06 + i] = ('round', {'shape': 'spinner', 'a0': -a1, 'a1': -a0})
    for cp in range(0x1FB00, 0x1FBAF):
        if cp in TRIANGULAR_BLOCKS:
            table[cp] = ('triangles', {'shape': 'poly', 'shapes': TRIANGULAR_BLOCKS[cp]})
        elif cp == 0x1FB93:
            table[cp] = (
                'shade',
                {'shape': 'dither', 'kind': 'inverse', 'half': 'e', 'fill_rest': True},
            )
        elif cp in (0x1FB95, 0x1FB96):
            table[cp] = ('shade', {'shape': 'checker', 'inverse': cp == 0x1FB96})
        elif cp == 0x1FB97:
            table[cp] = ('shade', {'shape': 'stripes'})
        elif cp in (0x1FB98, 0x1FB99):
            table[cp] = (
                'shade',
                {'shape': 'hatch', 'direction': 'nw-se' if cp == 0x1FB98 else 'ne-sw'},
            )
        elif 0x1FB9C <= cp <= 0x1FB9F:
            table[cp] = (
                'shade',
                {'shape': 'triangular', 'corner': ('nw', 'ne', 'se', 'sw')[cp - 0x1FB9C]},
            )
        else:
            table[cp] = legacy_computing(cp)
    for cp in range(0x1FBCE, 0x1FBF0):
        table[cp] = (
            ('grid', {'shape': 'blocks', 'boxes': [QUARTER_BLOCKS[cp]]})
            if cp in QUARTER_BLOCKS
            else legacy_computing(cp)
        )
    for cp in range(0x1CC1B, 0x1CC40):
        if cp in STUBS:
            table[cp] = ('grid', {'shape': 'blocks', 'boxes': STUBS[cp]})
        elif cp in QUARTER_GRID:
            col, row = QUARTER_GRID[cp]
            table[cp] = ('round', {'shape': 'grid_arc', 'n': 2, 'col': col, 'row': row})
        else:
            table[cp] = supplement(cp)
    for cp in range(0x1CD00, 0x1CDE6):
        table[cp] = supplement(cp)
    for cp in range(0x1CE16, 0x1CE1A):
        table[cp] = ('grid', {'shape': 'blocks', 'boxes': STUBS[cp]})
    for cp in range(0x1CE51, 0x1CEB0):
        table[cp] = supplement(cp)
    table.update(BRANCH)
    for cp, parts in BRANCH_CORNERS.items():
        line = parts[0] if parts[0] in ('v', 'h') else None
        table[cp] = (
            'round',
            {
                'shape': 'corners',
                'arms': [BRANCH_CORNER[p] for p in parts if p in BRANCH_CORNER],
                'line': line,
            },
        )
    for i, lines in enumerate(COMMIT_LINES):
        table[0xF5EE + 2 * i] = ('round', {'shape': 'commit', 'lines': lines, 'solid': True})
        table[0xF5EF + 2 * i] = ('round', {'shape': 'commit', 'lines': lines, 'solid': False})
    return table


TABLE = build()


def generated_ranges() -> list[str]:
    """Contiguous runs of the table's codepoints in table order, as 'XXXX' or 'XXXX-YYYY'."""
    out: list[str] = []
    start = prev = None
    for cp in [*TABLE, None]:
        if start is not None and (cp is None or cp != prev + 1):
            out.append(f'{start:04X}' if start == prev else f'{start:04X}-{prev:04X}')
            start = None
        if cp is not None and start is None:
            start = cp
        prev = cp
    return out
