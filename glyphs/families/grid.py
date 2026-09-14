"""Grid fills: blocks, quadrants, sextants, octants, sixteenths and eighth bars.

`cells` is a mask over a cols x rows lattice with row 0 at the TOP, the order Unicode numbers the
mosaic pieces in. Mosaic pieces are solid fractional blocks (they overhang the outer cell edges);
pattern lattices such as the shades span exactly the cell.
"""

from glyphs import cell
from glyphs.contour import Contour, rect


def _merge_rows(
    cols: int, rows: int, mask: set[tuple[int, int]]
) -> list[tuple[int, int, int, int]]:
    """Filled cells as (col0, col1, row0, row1) rectangles, runs merged along both axes."""
    runs: list[tuple[int, int, int, int]] = []
    for row in range(rows):
        c = 0
        while c < cols:
            if (row, c) not in mask:
                c += 1
                continue
            end = c
            while end + 1 < cols and (row, end + 1) in mask:
                end += 1
            above = [i for i, run in enumerate(runs) if run[:2] == (c, end) and run[3] == row]
            if above:
                runs[above[0]] = (c, end, runs[above[0]][2], row + 1)
            else:
                runs.append((c, end, row, row + 1))
            c = end + 1
    return runs


def cells(
    cols: int, rows: int, mask: set[tuple[int, int]], *, solid: bool = False, inset: int = 0
) -> list[Contour]:
    xs, ys = cell.x_bounds(cols), cell.y_bounds(rows)
    out: list[Contour] = []
    for c0, c1, r0, r1 in _merge_rows(cols, rows, mask):
        x0, x1 = xs[c0] + inset, xs[c1 + 1] - inset
        y0, y1 = ys[rows - r1] + inset, ys[rows - r0] - inset
        if solid:
            x0, x1, y0, y1 = cell.overhang(x0, x1, y0, y1)
        out.append(rect(x0, x1, y0, y1))
    return out


def block(x0: int, x1: int, y0: int, y1: int) -> list[Contour]:
    """A solid rectangle in lattice coordinates."""
    return [rect(*cell.overhang(x0, x1, y0, y1))]


def eighths(*, cols: set[int] = frozenset(), rows: set[int] = frozenset()) -> list[Contour]:
    """Full-height eighth columns and full-width eighth rows, numbered 1-8 from the left / top."""
    xs, ys = cell.x_bounds(8), cell.y_bounds(8)
    out = [
        rect(*cell.overhang(xs[c - 1], xs[c], cell.BOTTOM_UNITS, cell.LATTICE_TOP_UNITS))
        for c in sorted(cols)
    ]
    out += [rect(*cell.overhang(0, cell.ADVANCE_UNITS, ys[8 - r], ys[9 - r])) for r in sorted(rows)]
    return out


def draw(params: dict) -> list[Contour]:
    shape = params['shape']
    if shape == 'cells':
        return cells(
            params['cols'],
            params['rows'],
            params['mask'],
            solid=params.get('solid', False),
            inset=params.get('inset', 0),
        )
    if shape == 'blocks':
        return [c for box_ in params['boxes'] for c in block(*box_)]
    if shape == 'eighths':
        return eighths(cols=params.get('cols', frozenset()), rows=params.get('rows', frozenset()))
    raise ValueError(shape)
