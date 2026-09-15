"""Oracle (f) junctions between the overlay and the companion: a kept stroke tiles across the row
seam, and a kept junction's arm lands on the pixel rows the companion's own dashes do.

Both margins are learned per run from `ink_floor` (the solid level less MAX_BOUNDARY_LOSS), never
an absolute ink level; a failure prints `Term.diagnose` so CI alone is actionable.
"""

import math
import statistics

from tests.render.conftest import MAX_BOUNDARY_LOSS

CELL_WIDTH_PX = 1240 / 2000 * 14
LINE_HEIGHT_PX = 17
STACK = 3
BLOCK = '#block'
SPAN = '#block .row span'
FAINT = 0.05


def column_with_most_ink(grid: list[list[float]]) -> int:
    return max(range(len(grid[0])), key=lambda x: sum(row[x] for row in grid))


def rows_around(boundary: float, height: int) -> list[int]:
    """The device pixel row the boundary falls in and its two neighbours."""
    return [y for y in (int(boundary) - 1, int(boundary), int(boundary) + 1) if 0 <= y < height]


def test_stacked_light_vertical_leaves_no_seam_row(term, ink_floor):
    """Mutation: a build with OVERHANG_UNITS = 0, whose `│` stops at the cell edge, composites two
    partial coverages on the boundary row and loses 14 to 31% of the stroke there at DPR 1 in all
    three engines (a zoom of 1.0 included, because the 17 px row and the 13.5 px baseline put the
    stroke's end inside a device row). The companion's own `│` does NOT fail this: its bottom
    overshoots the Blink and Gecko rows by 39 and 110 units and covers the boundary row that its
    top stops 29 units short of, so a companion-only stack beads rather than dips."""
    term.set_rows('term', [['\u2502']] * STACK)
    grid = term.ink(BLOCK)
    x = column_with_most_ink(grid)
    column = [row[x] for row in grid]
    interior = statistics.median(column)
    allowance = term.solid_level() * MAX_BOUNDARY_LOSS
    for k in range(1, STACK):
        for y in rows_around(k * LINE_HEIGHT_PX * term.scale, len(grid)):
            assert column[y] >= interior - allowance, term.diagnose(grid, y, x, ink_floor, SPAN)


def cell_columns(index: int, scale: float, width: int) -> range:
    """The device pixel columns lying wholly inside cell `index`."""
    left, right = index * CELL_WIDTH_PX * scale, (index + 1) * CELL_WIDTH_PX * scale
    return range(max(0, math.ceil(left)), min(width, math.floor(right)))


def row_profile(grid: list[list[float]], columns: list[int]) -> list[float]:
    return [sum(row[x] for x in columns) / len(columns) for row in grid]


def inked_columns(grid: list[list[float]], columns: range, row: int, *, below: float) -> list[int]:
    """The columns of a cell whose ink at `row` is below the given level."""
    return [x for x in columns if grid[row][x] < below]


def arm_profiles(term, cls: str) -> tuple[list[float], list[float], list[float], list[list[float]]]:
    """(cell 0 cross, companion dash, cell 2 cross, grid) per-row mean ink of `┼┄┼` under `cls`:
    the crosses read over the columns free of their vertical stroke, the dash over the columns
    inside a dash segment (at least 90% of its fullest column)."""
    term.set_rows(cls, [['\u253c\u2504\u253c']])
    grid = term.ink(BLOCK)
    width, height = len(grid[0]), len(grid)
    middle = cell_columns(1, term.scale, width)
    column_ink = {x: sum(row[x] for row in grid) for x in middle}
    segment = [x for x in middle if column_ink[x] >= 0.9 * max(column_ink.values())]
    reference = row_profile(grid, segment)
    arm_row = max(range(height), key=reference.__getitem__)
    far_row = 1 if arm_row > height // 2 else height - 2
    crosses = []
    for index in (0, 2):
        columns = inked_columns(grid, cell_columns(index, term.scale, width), far_row, below=FAINT)
        assert columns, f'cell {index} has no column free of the vertical stroke'
        crosses.append(row_profile(grid, columns))
    return crosses[0], reference, crosses[1], grid


def rows_at(profile: list[float], level: float) -> set[int]:
    return {y for y, v in enumerate(profile) if v >= level}


def test_cross_arm_row_equals_the_companion_dash(term, ink_floor):
    """`┼┄┼`: the crosses are ours, the light triple dash between them is the companion's, on the
    companion's own midline. Over the columns that carry no vertical stroke, the crosses' per-row
    ink has to be the same set of rows at the same level as the dash's segments. The per-row
    allowance is learned from the companion's OWN cross beside its own dash in the same run: the
    rasterizer paints the fringe row of a cross and of a lone horizontal a little differently even
    within one font (measured 0.15 of solid in Chromium at DPR 1), and that much is not a junction
    defect. Mutation: a cross drawn on the lattice centre (y 714) rather than the companion's
    midline (645) steps half a device row at DPR 1."""
    solid = term.solid_level()
    own_left, own_reference, own_right, _ = arm_profiles(term, 'base')
    noise = max(
        abs(a - b) for own in (own_left, own_right) for a, b in zip(own, own_reference, strict=True)
    )
    allowance = max(MAX_BOUNDARY_LOSS * solid, noise)
    left, reference, right, grid = arm_profiles(term, 'term')
    expected = rows_at(reference, 0.5 * solid)
    for index, profile in ((0, left), (2, right)):
        column = next(iter(cell_columns(index, term.scale, len(grid[0]))))
        inked = rows_at(profile, 0.5 * solid)
        assert inked == expected, (
            f'cell {index} arm rows {sorted(inked)} against the companion dash '
            f'{sorted(expected)}\n{term.diagnose(grid, max(expected), column, ink_floor, SPAN)}'
        )
        for y, (ours, theirs) in enumerate(zip(profile, reference, strict=True)):
            assert abs(ours - theirs) <= allowance, (
                f'cell {index} row {y}: {ours:.3f} against the companion {theirs:.3f}, allowance '
                f'{allowance:.3f}\n{term.diagnose(grid, y, column, ink_floor, SPAN)}'
            )
