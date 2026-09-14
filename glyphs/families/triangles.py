"""Filled triangles: mosaic wedges, powerline arrows, triangular blocks and geometric corners.

Shapes are the cell rectangle clipped by half-planes; every vertex left on a cell edge then takes
the overhang, so the slanted edge of a wedge meets its neighbour's slightly inside the seam.
"""

from glyphs import cell
from glyphs.contour import Contour, clip, half_plane, polygon

FRAME = [
    (0, cell.BOTTOM_UNITS),
    (cell.ADVANCE_UNITS, cell.BOTTOM_UNITS),
    (cell.ADVANCE_UNITS, cell.LATTICE_TOP_UNITS),
    (0, cell.LATTICE_TOP_UNITS),
]


def at(fx: float, fy: float) -> tuple[float, float]:
    """A cell point from fractions of the width and of the height, both from the bottom-left."""
    return fx * cell.ADVANCE_UNITS, cell.BOTTOM_UNITS + fy * cell.LATTICE_HEIGHT_UNITS


def _solid(points: list[tuple[float, float]], *, pin: tuple[float, float] | None = None) -> Contour:
    """Overhang the vertices on cell edges except `pin`, a vertex that must stay in place."""
    out = []
    for x, y in points:
        if pin is not None and abs(x - pin[0]) < 1 and abs(y - pin[1]) < 1:
            out.append((x, y))
        else:
            out.append((cell.edge_x(round(x)), cell.edge_y(round(y))))
    return polygon(out)


def wedge(
    p: tuple[float, float], q: tuple[float, float], keep: tuple[float, float]
) -> list[Contour]:
    """The cell cut by the line p-q, keeping the side that holds `keep`; all `at` fractions."""
    a, b, c = half_plane(at(*p), at(*q), 1)
    kx, ky = at(*keep)
    side = 1 if a * kx + b * ky + c > 0 else -1
    return [c for c in [_solid(clip(list(FRAME), *half_plane(at(*p), at(*q), side)))] if c]


def poly(*shapes: list[tuple[float, float]]) -> list[Contour]:
    """Solid polygons given as `at` fractions."""
    return [_solid([at(*p) for p in shape]) for shape in shapes]


def arrow(direction: str, *, inverted: bool = False) -> list[Contour]:
    """Powerline: a full-height triangle whose apex touches the far edge's midpoint; inverted is
    the two corner triangles left over."""
    apex_x = cell.ADVANCE_UNITS if direction == 'e' else 0
    base_x = 0 if direction == 'e' else cell.ADVANCE_UNITS
    apex = (apex_x, cell.MIDLINE_Y)
    top, bottom = (base_x, cell.LATTICE_TOP_UNITS), (base_x, cell.BOTTOM_UNITS)
    if not inverted:
        return [_solid([bottom, top, apex], pin=apex)]
    far_top, far_bottom = (apex_x, cell.LATTICE_TOP_UNITS), (apex_x, cell.BOTTOM_UNITS)
    return [_solid([top, far_top, apex]), _solid([bottom, apex, far_bottom])]


def draw(params: dict) -> list[Contour]:
    shape = params['shape']
    if shape == 'wedge':
        return wedge(params['p'], params['q'], params['keep'])
    if shape == 'poly':
        return poly(*params['shapes'])
    if shape == 'arrow':
        return arrow(params['direction'], inverted=params.get('inverted', False))
    raise ValueError(shape)
