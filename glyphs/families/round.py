"""Rounded shapes: box-drawing arcs, circles, powerline half-discs, spinners, progress bars,
justified circle parts, the twelfth-circle grid and kitty's commit markers.

Angles are degrees, counter-clockwise from +x with y up. Shapes that join a box stroke (the arcs,
the commit markers) sit on the companion's MIDLINE_Y; shapes that join nothing are centred on
the cell, CENTRE_Y.
"""

import math

from glyphs import cell
from glyphs.contour import Contour, arc, arc_band, arc_start, ellipse, rect, ring
from glyphs.families.strokes import HALF_LIGHT, box

RADIUS = cell.ADVANCE_UNITS // 2
INNER = RADIUS - cell.LIGHT_STROKE_UNITS
CX = cell.CENTRE_X
SIGN = {'n': 1, 's': -1, 'e': 1, 'w': -1}


def corner(vertical: str, horizontal: str) -> list[Contour]:
    """A light quarter-circle arc of radius RADIUS joining the `vertical` and `horizontal` arms,
    plus the straight stubs from the arc's tangent points to the cell edges."""
    sx, sy = SIGN[horizontal], SIGN[vertical]
    cx, cy = CX + sx * RADIUS, cell.MIDLINE_Y + sy * RADIUS
    a_vertical = 180 if sx > 0 else 360
    a_horizontal = 270 if sy > 0 else 90
    if a_vertical - a_horizontal > 180:
        a_vertical = 0
    out = [arc_band(cx, cy, RADIUS + HALF_LIGHT, RADIUS - HALF_LIGHT, a_vertical, a_horizontal)]
    y_edge = cell.TOP_OVERHANG if sy > 0 else cell.BOTTOM_OVERHANG
    out.append(rect(CX - HALF_LIGHT, CX + HALF_LIGHT, min(cy, y_edge), max(cy, y_edge)))
    x_edge = cell.RIGHT_OVERHANG if sx > 0 else cell.LEFT_OVERHANG
    if x_edge != cx:
        out.append(
            rect(
                min(cx, x_edge),
                max(cx, x_edge),
                cell.MIDLINE_Y - HALF_LIGHT,
                cell.MIDLINE_Y + HALF_LIGHT,
            )
        )
    return out


def corners(arms: list[tuple[str, str]], line: str | None = None) -> list[Contour]:
    out = [c for v, h in arms for c in corner(v, h)]
    if line == 'v':
        out += box(n='light', s='light')
    elif line == 'h':
        out += box(e='light', w='light')
    return out


def circle(kind: str) -> list[Contour]:
    cy = cell.CENTRE_Y
    if kind == 'white':
        return ring(CX, cy, RADIUS, INNER)
    if kind == 'black':
        return [ellipse(CX, cy, RADIUS, RADIUS)]
    return [*ring(CX, cy, RADIUS, INNER), ellipse(CX, cy, RADIUS // 2, RADIUS // 2)]


def half_disc(bulge: str, *, outline: bool = False) -> list[Contour]:
    """Powerline D: a half-ellipse spanning the overhung cell height, flat side on the far edge."""
    ry = (cell.TOP_OVERHANG - cell.BOTTOM_OVERHANG) / 2
    rx = cell.ADVANCE_UNITS
    cx = 0 if bulge == 'e' else rx
    a0, a1 = (-90, 90) if bulge == 'e' else (90, 270)
    flat = cell.LEFT_OVERHANG if bulge == 'e' else cell.RIGHT_OVERHANG
    cy = cell.CENTRE_Y
    if outline:
        d = cell.LIGHT_STROKE_UNITS
        return [
            [
                arc_start(cx, cy, rx, ry, a0),
                *arc(cx, cy, rx, ry, a0, a1),
                arc_start(cx, cy, rx - d, ry - d, a1),
                *arc(cx, cy, rx - d, ry - d, a1, a0),
            ]
        ]
    first, last = (
        (cell.BOTTOM_OVERHANG, cell.TOP_OVERHANG)
        if bulge == 'e'
        else (cell.TOP_OVERHANG, cell.BOTTOM_OVERHANG)
    )
    return [
        [(flat, first), arc_start(cx, cy, rx, ry, a0), *arc(cx, cy, rx, ry, a0, a1), (flat, last)]
    ]


def spinner(a0: float, a1: float) -> list[Contour]:
    return [arc_band(CX, cell.CENTRE_Y, RADIUS, INNER, a0, a1)]


def progress(part: str, *, filled: bool) -> list[Contour]:
    """A capsule of diameter RADIUS * 2 centred on the cell; `part` is its w end, middle or e
    end. Filled adds an inner bar one stroke inside the outline."""
    cy = cell.CENTRE_Y
    top, bottom = cy + RADIUS, cy - RADIUS
    inner_r = RADIUS - 2 * cell.LIGHT_STROKE_UNITS
    x0, x1 = cell.LEFT_OVERHANG, cell.RIGHT_OVERHANG
    out: list[Contour] = []
    if part == 'w':
        x0 = CX
        out.append(arc_band(CX, cy, RADIUS, INNER, 90, 270))
        if filled:
            out.append(
                [arc_start(CX, cy, inner_r, inner_r, 90), *arc(CX, cy, inner_r, inner_r, 90, 270)]
            )
    elif part == 'e':
        x1 = CX
        out.append(arc_band(CX, cy, RADIUS, INNER, -90, 90))
        if filled:
            out.append(
                [arc_start(CX, cy, inner_r, inner_r, -90), *arc(CX, cy, inner_r, inner_r, -90, 90)]
            )
    out.append(rect(x0, x1, top - cell.LIGHT_STROKE_UNITS, top))
    out.append(rect(x0, x1, bottom, bottom + cell.LIGHT_STROKE_UNITS))
    if filled:
        out.append(rect(x0, x1, cy - inner_r, cy + inner_r))
    return out


def justified(edge: str, *, outline: bool = False) -> list[Contour]:
    """A half circle of radius RADIUS whose diameter lies on the named cell edge, filled or as a
    light ring; the flat side and the ring ends take the overhang."""
    cx = {'n': CX, 's': CX, 'w': 0, 'e': cell.ADVANCE_UNITS}[edge]
    cy = {
        'n': cell.LATTICE_TOP_UNITS,
        's': cell.BOTTOM_UNITS,
        'w': cell.CENTRE_Y,
        'e': cell.CENTRE_Y,
    }[edge]
    a0 = {'n': 180, 's': 0, 'w': -90, 'e': 90}[edge]
    if not outline:
        if edge in 'ns':
            strip = rect(cx - RADIUS, cx + RADIUS, *sorted((cy, cell.edge_y(cy))))
        else:
            strip = rect(*sorted((cx, cell.edge_x(cx))), cy - RADIUS, cy + RADIUS)
        return [
            [arc_start(cx, cy, RADIUS, RADIUS, a0), *arc(cx, cy, RADIUS, RADIUS, a0, a0 + 180)],
            strip,
        ]
    band = arc_band(cx, cy, RADIUS, INNER, a0, a0 + 180)
    caps: list[Contour] = []
    for x, y in (
        arc_start(cx, cy, RADIUS, RADIUS, a0),
        arc_start(cx, cy, RADIUS, RADIUS, a0 + 180),
    ):
        if edge in 'ns':
            lo, hi = sorted((x, cx + (INNER if x > cx else -INNER)))
            caps.append(rect(lo, hi, min(cy, cell.edge_y(cy)), max(cy, cell.edge_y(cy))))
        else:
            lo, hi = sorted((y, cy + (INNER if y > cy else -INNER)))
            caps.append(rect(min(cx, cell.edge_x(cx)), max(cx, cell.edge_x(cx)), lo, hi))
    return [band, *caps]


def quarter(corner_name: str) -> list[Contour]:
    """A filled quarter circle of radius RADIUS centred on the named cell corner."""
    cx = 0 if 'w' in corner_name else cell.ADVANCE_UNITS
    cy = cell.LATTICE_TOP_UNITS if 'n' in corner_name else cell.BOTTOM_UNITS
    a0 = {'ne': 180, 'nw': 270, 'sw': 0, 'se': 90}[corner_name]
    p0 = arc_start(cx, cy, RADIUS, RADIUS, a0)
    p1 = arc_start(cx, cy, RADIUS, RADIUS, a0 + 90)
    push = [(cell.edge_x(x), cell.edge_y(y)) for x, y in (p1, (cx, cy), p0)]
    return [[p0, *arc(cx, cy, RADIUS, RADIUS, a0, a0 + 90), *push]]


def grid_arc(n: int, col: int, row: int) -> list[Contour]:
    """This cell's light arc of the ellipse inscribed in an n x n cell block, each edge of the
    band ending where it crosses the overhung cell frame so neighbouring pieces overlap."""
    w, h = cell.ADVANCE_UNITS, cell.LATTICE_HEIGHT_UNITS
    cx, cy = (n / 2 - col) * w, cell.LATTICE_TOP_UNITS - (n / 2 - row) * h
    rx, ry = n / 2 * w, n / 2 * h
    sector = 90 // (n - 1)
    for k in range(360 // sector):
        m = math.radians(k * sector + sector / 2)
        x, y = cx + rx * math.cos(m), cy + ry * math.sin(m)
        if 0 <= x <= w and cell.BOTTOM_UNITS <= y <= cell.LATTICE_TOP_UNITS:
            break
    else:
        raise ValueError((n, col, row))
    a0, a1 = k * sector, (k + 1) * sector
    d = cell.LIGHT_STROKE_UNITS
    ends = [_frame_line(cx, cy, rx, ry, a) for a in (a0, a1)]
    o0, o1 = (
        _frame_crossing(cx, cy, rx, ry, a, *line) for a, line in zip((a0, a1), ends, strict=True)
    )
    i0, i1 = (
        _frame_crossing(cx, cy, rx - d, ry - d, a, *line)
        for a, line in zip((a0, a1), ends, strict=True)
    )
    return [
        [
            arc_start(cx, cy, rx, ry, o0),
            *arc(cx, cy, rx, ry, o0, o1),
            arc_start(cx, cy, rx - d, ry - d, i1),
            *arc(cx, cy, rx - d, ry - d, i1, i0),
        ]
    ]


def _frame_line(cx: float, cy: float, rx: float, ry: float, a: float) -> tuple[str, int]:
    """The overhung frame line ('x' or 'y', value) that the cell edge under angle `a` extends to."""
    t = math.radians(a)
    x, y = cx + rx * math.cos(t), cy + ry * math.sin(t)
    if abs(x) < 1 or abs(x - cell.ADVANCE_UNITS) < 1:
        return 'x', cell.LEFT_OVERHANG if abs(x) < 1 else cell.RIGHT_OVERHANG
    return 'y', cell.BOTTOM_OVERHANG if abs(y - cell.BOTTOM_UNITS) < 1 else cell.TOP_OVERHANG


def _frame_crossing(
    cx: float, cy: float, rx: float, ry: float, a: float, axis: str, line: int
) -> float:
    """The angle nearest `a` at which the ellipse crosses the frame line."""
    if axis == 'x':
        base = math.degrees(math.acos(max(-1, min(1, (line - cx) / rx))))
        candidates = (base, -base, 360 - base)
    else:
        base = math.degrees(math.asin(max(-1, min(1, (line - cy) / ry))))
        candidates = (base, 180 - base, base + 360, -180 - base)
    return min(candidates, key=lambda c: abs(c - a))


def commit(lines: str, *, solid: bool) -> list[Contour]:
    """kitty's branch node: a circle at 0.9 of RADIUS with light stubs to the edges in `lines`."""
    r, cy = round(RADIUS * 0.9), cell.MIDLINE_Y
    out = [ellipse(CX, cy, r, r)] if solid else ring(CX, cy, r, r - cell.LIGHT_STROKE_UNITS)
    for side in lines:
        if side in 'ns':
            y0, y1 = (cy + r, cell.TOP_OVERHANG) if side == 'n' else (cell.BOTTOM_OVERHANG, cy - r)
            out.append(rect(CX - HALF_LIGHT, CX + HALF_LIGHT, y0, y1))
        else:
            x0, x1 = (CX + r, cell.RIGHT_OVERHANG) if side == 'e' else (cell.LEFT_OVERHANG, CX - r)
            out.append(rect(x0, x1, cy - HALF_LIGHT, cy + HALF_LIGHT))
    return out


def draw(params: dict) -> list[Contour]:
    shape = params['shape']
    if shape == 'corners':
        return corners(params['arms'], params.get('line'))
    if shape == 'circle':
        return circle(params['kind'])
    if shape == 'half_disc':
        return half_disc(params['bulge'], outline=params.get('outline', False))
    if shape == 'spinner':
        return spinner(params['a0'], params['a1'])
    if shape == 'progress':
        return progress(params['part'], filled=params['filled'])
    if shape == 'justified':
        return justified(params['edge'], outline=params.get('outline', False))
    if shape == 'quarter':
        return quarter(params['corner'])
    if shape == 'grid_arc':
        return grid_arc(params['n'], params['col'], params['row'])
    if shape == 'commit':
        return commit(params['lines'], solid=params['solid'])
    raise ValueError(shape)
