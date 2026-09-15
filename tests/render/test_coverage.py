"""Oracle (c) coverage: two solid glyphs that meet at a cell boundary leave no device pixel on that
boundary below the level this host paints full coverage at, at DPR 1 and 2, with or without page
zoom.

Both pairs form one solid rectangle of ink, so the check is that every pixel inside that
rectangle's ink bounds (two pixels in from its anti-aliased edges) reaches the `ink_floor` the run
measured for itself. It was an absolute 254/255, which held here and failed on the ubuntu-24.04
runner: rasterization there leaves 250/255 on the boundary column of a build whose overhang is
present and correct.
"""

from tests.render import pixels

EDGE = 2
CELL_WIDTH_PX = 1240 / 2000 * 14
LINE_HEIGHT_PX = 17
# A row's span carries the text, so it is both the one-row screenshot and the node CDP can name a
# painting font for; #block spans the two stacked rows but carries no text of its own.
SPAN = '#block .row span'
BLOCK = '#block'


def weakest_inside(grid: list[list[float]]) -> tuple[float, int, int]:
    x0, y0, x1, y1 = pixels.ink_box(grid)
    return min(
        (grid[y][x], y, x)
        for y in range(y0 + EDGE, y1 - EDGE + 1)
        for x in range(x0 + EDGE, x1 - EDGE + 1)
    )


def test_adjacent_full_blocks_leave_no_seam_column(term, ink_floor):
    """Mutation: OVERHANG_UNITS = 0 leaves the column on the fractional cell boundary at the
    composite of two partial coverages."""
    term.set_rows('term', [['██']])
    grid = term.ink(SPAN)
    box = pixels.ink_box(grid)
    assert box[2] - box[0] + 1 >= 2 * CELL_WIDTH_PX * term.scale - 1, box
    value, y, x = weakest_inside(grid)
    assert value >= ink_floor, term.diagnose(grid, y, x, ink_floor, SPAN)


def test_stacked_half_blocks_leave_no_seam_row(term, ink_floor):
    """A lower half block above an upper half block meet at the row boundary. Mutation:
    OVERHANG_UNITS = 0 leaves that device row partially covered wherever the boundary is not
    pixel-aligned, measured on all three engines at DPR 1 at both zooms and at DPR 2 zoom 1.1. At
    DPR 2 zoom 1.0 the boundary lands on an integer device row, so no seam can exist and that one
    parameter cannot see the mutation."""
    term.set_rows('term', [['▄'], ['▀']])
    grid = term.ink(BLOCK)
    box = pixels.ink_box(grid)
    assert box[3] - box[1] + 1 >= LINE_HEIGHT_PX * term.scale - 1, box
    value, y, x = weakest_inside(grid)
    assert value >= ink_floor, term.diagnose(grid, y, x, ink_floor, SPAN)


def test_companion_pair_fails_the_oracle(term, ink_floor):
    """The floor has to sit below what an unoverhung boundary reads, or the column check above
    could not fail: the companion's own full block stops at the cell edge. Only the column gets
    this pole, because the companion's stacked half blocks land pixel-aligned at DPR 2."""
    term.set_rows('base', [['██']])
    value, _, _ = weakest_inside(term.ink(SPAN))
    assert value < ink_floor, f'companion boundary at {value:.3f}, floor {ink_floor:.3f}'
