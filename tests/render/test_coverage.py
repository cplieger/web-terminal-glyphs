"""Oracle (c) coverage: two solid glyphs that meet at a cell boundary leave no device pixel on that
boundary below full ink at DPR 1 and 2, with or without page zoom.

Both pairs form one solid rectangle of ink, so the check is that every pixel inside that
rectangle's ink bounds (two pixels in from its anti-aliased edges) is the glyph colour."""

FULL = 254 / 255
EDGE = 2
CELL_WIDTH_PX = 1240 / 2000 * 14
LINE_HEIGHT_PX = 17


def ink_box(grid) -> tuple[int, int, int, int]:
    cells = [(x, y) for y, row in enumerate(grid) for x, v in enumerate(row) if v >= 0.5]
    xs, ys = [x for x, _ in cells], [y for _, y in cells]
    return min(xs), min(ys), max(xs), max(ys)


def weakest_inside(grid) -> tuple[float, int, int, tuple[int, int, int, int]]:
    box = ink_box(grid)
    x0, y0, x1, y1 = box
    weakest = min(
        (grid[y][x], y, x)
        for y in range(y0 + EDGE, y1 - EDGE + 1)
        for x in range(x0 + EDGE, x1 - EDGE + 1)
    )
    return (*weakest, box)


def test_adjacent_full_blocks_leave_no_seam_column(term):
    """Mutation: OVERHANG_UNITS = 0 leaves the column on the fractional cell boundary at the
    composite of two partial coverages."""
    term.set_rows('term', [['██']])
    value, y, x, box = weakest_inside(term.ink('#block .row span'))
    assert box[2] - box[0] + 1 >= 2 * CELL_WIDTH_PX * term.scale - 1, box
    assert value >= FULL, f'ink {value:.3f} at column {x}, row {y}; ink box {box}'


def test_stacked_half_blocks_leave_no_seam_row(term):
    """A lower half block above an upper half block meet at the row boundary. Mutation:
    OVERHANG_UNITS = 0 leaves that device row partially covered wherever the boundary is not
    pixel-aligned, which Blink's 13.0px baseline makes true even at zoom 1."""
    term.set_rows('term', [['▄'], ['▀']])
    value, y, x, box = weakest_inside(term.ink('#block'))
    assert box[3] - box[1] + 1 >= LINE_HEIGHT_PX * term.scale - 1, box
    assert value >= FULL, f'ink {value:.3f} at row {y}, column {x}; ink box {box}'
