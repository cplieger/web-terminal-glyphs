"""Stroke sets: box drawing (light, heavy, dashed, double, diagonal) and kitty's branch lines.

Arms are named n, s, e, w. `box` takes a weight per arm ('light', 'heavy' or None); `double_box`
takes a stroke count per arm (0, 1 or 2).
"""

from itertools import pairwise

from glyphs import cell
from glyphs.contour import Contour, clip, half_plane, polygon, rect

HALF_LIGHT = cell.LIGHT_STROKE_UNITS // 2
DOUBLE_OFFSET = cell.LIGHT_STROKE_UNITS // 2 + cell.DOUBLE_GAP_UNITS // 2

# Per axis: the cross-axis centre, the along-axis centre and the along-axis overhang edges.
AXIS = {
    'v': (cell.CENTRE_X, cell.MIDLINE_Y, cell.BOTTOM_OVERHANG, cell.TOP_OVERHANG),
    'h': (cell.MIDLINE_Y, cell.CENTRE_X, cell.LEFT_OVERHANG, cell.RIGHT_OVERHANG),
}


def _rect(axis: str, along0: int, along1: int, cross0: int, cross1: int) -> Contour:
    if axis == 'v':
        return rect(cross0, cross1, along0, along1)
    return rect(along0, along1, cross0, cross1)


def box(
    n: str | None = None, s: str | None = None, e: str | None = None, w: str | None = None
) -> list[Contour]:
    """Light/heavy arms from the cell edge to the centre, plus the centre square that joins them,
    sized to the widest arm on each axis so a heavy arm ends flush with the crossing stroke."""
    out: list[Contour] = []
    for axis, plus, minus in (('v', n, s), ('h', e, w)):
        cross, along, lo, hi = AXIS[axis]
        if plus and plus == minus:
            half = cell.STROKE_UNITS[plus] // 2
            out.append(_rect(axis, lo, hi, cross - half, cross + half))
            continue
        for arm, a0, a1 in ((plus, along, hi), (minus, lo, along)):
            if arm:
                half = cell.STROKE_UNITS[arm] // 2
                out.append(_rect(axis, a0, a1, cross - half, cross + half))
    v_width = max((cell.STROKE_UNITS[a] for a in (n, s) if a), default=0)
    h_width = max((cell.STROKE_UNITS[a] for a in (e, w) if a), default=0)
    if v_width and h_width:
        out.append(
            rect(
                cell.CENTRE_X - v_width // 2,
                cell.CENTRE_X + v_width // 2,
                cell.MIDLINE_Y - h_width // 2,
                cell.MIDLINE_Y + h_width // 2,
            )
        )
    return out


def dashed(axis: str, weight: str, dashes: int) -> list[Contour]:
    cross, _, _, _ = AXIS[axis]
    half = cell.STROKE_UNITS[weight] // 2
    if axis == 'v':
        bounds, half_gap = cell.y_bounds(dashes), cell.LATTICE_HEIGHT_UNITS // 16
    else:
        bounds, half_gap = cell.x_bounds(dashes), cell.ADVANCE_UNITS // 16
    return [
        _rect(axis, a0 + half_gap, a1 - half_gap, cross - half, cross + half)
        for a0, a1 in pairwise(bounds)
    ]


def _positions(centre: int, count: int) -> list[int]:
    if count == 1:
        return [centre]
    return [centre - DOUBLE_OFFSET, centre + DOUBLE_OFFSET] if count == 2 else []


def _axis_segments(
    axis: str, plus: int, minus: int, side_plus: int, side_minus: int
) -> list[Contour]:
    """Strokes along one axis. `plus`/`minus` are this axis's arm counts toward the +/- along
    direction; `side_plus`/`side_minus` the perpendicular arms toward the +/- cross direction."""
    cross, along, lo, hi = AXIS[axis]
    out: list[Contour] = []
    for arm, other, a_edge, sign in ((plus, minus, hi, 1), (minus, plus, lo, -1)):
        for x in _positions(cross, arm):
            side = side_plus if x > cross else side_minus
            if arm == other:
                if sign < 0:
                    continue
                if arm == 2 and side == 2:
                    out.append(_rect(axis, lo, along - HALF_LIGHT, x - HALF_LIGHT, x + HALF_LIGHT))
                    out.append(_rect(axis, along + HALF_LIGHT, hi, x - HALF_LIGHT, x + HALF_LIGHT))
                else:
                    out.append(_rect(axis, lo, hi, x - HALF_LIGHT, x + HALF_LIGHT))
                continue
            perp = _positions(
                along, side_plus if side_plus == side_minus else max(side_plus, side_minus)
            )
            if side_plus == side_minus:
                stop = max(perp) if sign > 0 else min(perp)
            else:
                outer_stroke = x == (cross - DOUBLE_OFFSET if side_plus else cross + DOUBLE_OFFSET)
                outer_line = min(perp) if sign > 0 else max(perp)
                inner_line = max(perp) if sign > 0 else min(perp)
                partner = (
                    inner_line if (arm == 2 and len(perp) == 2 and not outer_stroke) else outer_line
                )
                stop = partner - sign * HALF_LIGHT
            a0, a1 = (stop, a_edge) if sign > 0 else (a_edge, stop)
            out.append(_rect(axis, a0, a1, x - HALF_LIGHT, x + HALF_LIGHT))
    return out


def double_box(n: int = 0, s: int = 0, e: int = 0, w: int = 0) -> list[Contour]:
    """Single and double light arms: a stroke crosses a single perpendicular line, stops at the far
    edge of its paired double line, and a double through-line breaks between a double side arm."""
    return _axis_segments('v', n, s, e, w) + _axis_segments('h', e, w, n, s)


OVERHUNG_FRAME = [
    half_plane(
        (cell.LEFT_OVERHANG, cell.BOTTOM_OVERHANG), (cell.RIGHT_OVERHANG, cell.BOTTOM_OVERHANG), 1
    ),
    half_plane(
        (cell.RIGHT_OVERHANG, cell.BOTTOM_OVERHANG), (cell.RIGHT_OVERHANG, cell.TOP_OVERHANG), 1
    ),
    half_plane(
        (cell.RIGHT_OVERHANG, cell.TOP_OVERHANG), (cell.LEFT_OVERHANG, cell.TOP_OVERHANG), 1
    ),
    half_plane(
        (cell.LEFT_OVERHANG, cell.TOP_OVERHANG), (cell.LEFT_OVERHANG, cell.BOTTOM_OVERHANG), 1
    ),
]


def _on_edge(p: tuple[float, float]) -> bool:
    return p[0] in (0, cell.ADVANCE_UNITS) or p[1] in (cell.BOTTOM_UNITS, cell.LATTICE_TOP_UNITS)


def _band(p: tuple[float, float], q: tuple[float, float], lo: float, hi: float) -> Contour:
    """The strip between offsets lo and hi from the line p-q, clipped to the overhung frame and,
    at an endpoint inside the cell, cut square there."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = (dx * dx + dy * dy) ** 0.5
    ux, uy, nx, ny = dx / n, dy / n, -dy / n, dx / n
    reach = 2 * (cell.ADVANCE_UNITS + cell.LATTICE_HEIGHT_UNITS)
    band = [
        (p[0] - ux * reach + nx * lo, p[1] - uy * reach + ny * lo),
        (p[0] - ux * reach + nx * hi, p[1] - uy * reach + ny * hi),
        (q[0] + ux * reach + nx * hi, q[1] + uy * reach + ny * hi),
        (q[0] + ux * reach + nx * lo, q[1] + uy * reach + ny * lo),
    ]
    planes = list(OVERHUNG_FRAME)
    if not _on_edge(p):
        planes.append((ux, uy, -(ux * p[0] + uy * p[1])))
    if not _on_edge(q):
        planes.append((-ux, -uy, ux * q[0] + uy * q[1]))
    for plane in planes:
        band = clip(band, *plane)
    return polygon(band)


def diagonal(points: list[tuple[int, int]], weight: str = 'light') -> list[Contour]:
    """A polyline of thick segments; a segment end on a cell edge runs on to the overhung frame."""
    half = cell.STROKE_UNITS[weight] // 2
    return [c for p, q in pairwise(points) if (c := _band(p, q, -half, half))]


def double_diagonal(p: tuple[int, int], q: tuple[int, int]) -> list[Contour]:
    """Two light lines DOUBLE_GAP apart astride the corner-to-corner line p-q."""
    return [
        _band(p, q, offset - HALF_LIGHT, offset + HALF_LIGHT)
        for offset in (-DOUBLE_OFFSET, DOUBLE_OFFSET)
    ]


def fading(axis: str, count: int, toward: str) -> list[Contour]:
    """kitty's fading branch line: `count` segments shrinking toward the `toward` edge."""
    cross, _, _, _ = AXIS[axis]
    length = cell.LATTICE_HEIGHT_UNITS if axis == 'v' else cell.ADVANCE_UNITS
    start = cell.BOTTOM_UNITS if axis == 'v' else 0
    step = length / count
    out: list[Contour] = []
    for i in range(count):
        size = step * (count - i) / (count + 1)
        a0 = (
            start + i * step
            if toward in ('e', 'n')
            else start + length - (i + 1) * step + (step - size)
        )
        a1 = a0 + size
        out.append(_rect(axis, round(a0), round(a1), cross - HALF_LIGHT, cross + HALF_LIGHT))
    return out


def draw(params: dict) -> list[Contour]:
    shape = params['shape']
    if shape == 'box':
        return box(params.get('n'), params.get('s'), params.get('e'), params.get('w'))
    if shape == 'dashed':
        return dashed(params['axis'], params['weight'], params['dashes'])
    if shape == 'double':
        return double_box(
            params.get('n', 0), params.get('s', 0), params.get('e', 0), params.get('w', 0)
        )
    if shape == 'diagonal':
        return [
            c for line in params['lines'] for c in diagonal(line, params.get('weight', 'light'))
        ]
    if shape == 'double_diagonal':
        return double_diagonal(params['p'], params['q'])
    if shape == 'fading':
        return fading(params['axis'], params['count'], params['toward'])
    raise ValueError(shape)
