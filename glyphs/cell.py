"""The cell every glyph is drawn for, in font units at UPEM per em.

Frame: x in [0, ADVANCE_UNITS], y in [BOTTOM_UNITS, TOP_UNITS] from the baseline. At
CELL_FONT_SIZE_PX on a CELL_LINE_HEIGHT_PX row the baseline is CELL_BASELINE_PX below the row top
(the Gecko/WebKit frame; Blink puts it 0.5px higher). One CSS px is 142.857 units, so the row is
2428.57 units: the lattice pitch rounds down to LATTICE_HEIGHT_UNITS and the frame top rounds up,
leaving one unit above the lattice that only a solid glyph's overhang covers.

The six geometry rules every generator obeys:
1. A solid glyph extends OVERHANG_UNITS past each cell edge it touches and never past an internal
   boundary (`overhang`), so every boundary device pixel is fully inside one neighbour.
2. A lattice glyph spans exactly one cell pitch with an integer period allocation (`split`).
3. Fractional blocks land on `split` fractions; only their outer edges overhang.
4. Strokes are LIGHT/HEAVY_STROKE_UNITS; double is two light strokes DOUBLE_GAP_UNITS apart;
   dashes split a stroke into equal segments with equal gaps, half a gap at each edge.
5. Arcs and circles use the light stroke and a radius of half the cell width.
6. Every glyph advances ADVANCE_UNITS.
"""

UPEM = 2000
ADVANCE_UNITS = 1240
TOP_UNITS = 1929
BOTTOM_UNITS = -500
OVERHANG_UNITS = 72
LATTICE_HEIGHT_UNITS = 2428
LATTICE_TOP_UNITS = BOTTOM_UNITS + LATTICE_HEIGHT_UNITS

COMPANION_FAMILY = 'Monaspace Neon NF'
COMPANION_ASCENDER_UNITS = 1890
COMPANION_DESCENDER_UNITS = -400
COMPANION_LINE_GAP_UNITS = 200

CELL_FONT_SIZE_PX = 14
CELL_LINE_HEIGHT_PX = 17
CELL_BASELINE_PX = 13.5
CELL_RATIO = CELL_LINE_HEIGHT_PX / CELL_FONT_SIZE_PX

LIGHT_STROKE_UNITS = 160
HEAVY_STROKE_UNITS = 400
DOUBLE_GAP_UNITS = 160
STROKE_UNITS = {'light': LIGHT_STROKE_UNITS, 'heavy': HEAVY_STROKE_UNITS}

FAMILY_NAME = 'Web Terminal Glyphs'
POSTSCRIPT_NAME = 'WebTerminalGlyphs-Regular'
VERSION = '1.000'
COPYRIGHT = 'Copyright 2026 cplieger'
LICENSE_ID = 'Apache-2.0'
LICENSE_URL = 'https://www.apache.org/licenses/LICENSE-2.0'


def split(start: int, length: int, n: int) -> list[int]:
    """n + 1 integer boundaries dividing [start, start + length] into n parts, the remainder
    spread symmetrically (2428 / 3 -> 809, 810, 809; 2428 / 8 alternates 304, 303)."""
    return [start + (2 * k * length + n) // (2 * n) for k in range(n + 1)]


def x_bounds(n: int) -> list[int]:
    return split(0, ADVANCE_UNITS, n)


def y_bounds(n: int) -> list[int]:
    """Bottom to top."""
    return split(BOTTOM_UNITS, LATTICE_HEIGHT_UNITS, n)


CENTRE_X = x_bounds(2)[1]
MIDLINE_Y = y_bounds(2)[1]
LEFT_OVERHANG = -OVERHANG_UNITS
RIGHT_OVERHANG = ADVANCE_UNITS + OVERHANG_UNITS
BOTTOM_OVERHANG = BOTTOM_UNITS - OVERHANG_UNITS
TOP_OVERHANG = TOP_UNITS + OVERHANG_UNITS


def edge_x(x: int) -> int:
    """A solid coordinate on the left or right cell edge, moved out by the overhang."""
    if x <= 0:
        return LEFT_OVERHANG
    if x >= ADVANCE_UNITS:
        return RIGHT_OVERHANG
    return x


def edge_y(y: int) -> int:
    if y <= BOTTOM_UNITS:
        return BOTTOM_OVERHANG
    if y >= LATTICE_TOP_UNITS:
        return TOP_OVERHANG
    return y


def overhang(x0: int, x1: int, y0: int, y1: int) -> tuple[int, int, int, int]:
    return edge_x(x0), edge_x(x1), edge_y(y0), edge_y(y1)
