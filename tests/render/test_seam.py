"""Oracle (b) seam, on a 6 x 6 grid of one glyph per lattice family, with a margin learned per run
from two fixtures rendered in the same page: the overlay alone (good) and the companion alone
(bad); the subject is the production .term stack.

Pattern lattices (braille, the three shades) score the correlation of the grid with itself
shifted by the glyph's own period, on the weaker of the two axes: a pattern that continues across
cells scores near 1, one whose period does not divide the cell drops at every seam. Mosaic fills
(octant 2345678, sextant 23456) tile into a solid field with one notch per cell; they score the
share of the grid at full ink, and a seam is the extra absolute check: a pixel below the glyph
colour between two full-ink neighbours, which is what a boundary column at two partial coverages
looks like.
"""

import pytest

from tests.render import pixels

UNIT_PX = 14 / 2000
# Own period (vertical, horizontal) in font units: the octant pitch 607 x 620; the 25% and 75%
# dithers repeat every four 303.5-unit rows and every cell horizontally.
PERIODIC = {
    '\u28ff': (607, 620),
    '\u2591': (1214, 1240),
    '\u2592': (607, 620),
    '\u2593': (1214, 1240),
}
SOLID = ['\U0001cde5', '\U0001fb3b']
GRID = 6
FULL = 254 / 255
# Smallest separation measured across the three engines at DPR 1 and 2, zoom 1.0 and 1.1: 0.07,
# the dark shade in WebKit at DPR 2, where the companion's period is only 8% off the cell.
MIN_SEPARATION = 0.05


def periodicity(grid: list[list[float]], own_units: tuple[float, float], scale: float) -> float:
    own_v, own_h = own_units[0] * UNIT_PX * scale, own_units[1] * UNIT_PX * scale
    return min(
        pixels.correlation(grid, own_v, vertical=True),
        pixels.correlation(grid, own_h, vertical=False),
    )


def full_share(grid: list[list[float]]) -> float:
    return sum(v >= FULL for row in grid for v in row) / (len(grid) * len(grid[0]))


def weakest_dip(grid: list[list[float]]) -> float:
    """The weakest pixel that sits between two full-ink neighbours, along either axis; 1.0 when
    every such pixel is full."""
    dips = [1.0]
    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[y]) - 1):
            v = grid[y][x]
            if v < FULL and (
                (grid[y][x - 1] >= FULL and grid[y][x + 1] >= FULL)
                or (grid[y - 1][x] >= FULL and grid[y + 1][x] >= FULL)
            ):
                dips.append(v)
    return min(dips)


def measure(term, cls: str, glyph: str) -> tuple[float, float]:
    """(score for the learned margin, weakest seam dip) of the 6 x 6 grid under `cls`."""
    term.set_rows(cls, [[glyph * GRID]] * GRID)
    grid = pixels.crop_to_ink(term.ink('#block'))
    if glyph in PERIODIC:
        return periodicity(grid, PERIODIC[glyph], term.scale), 1.0
    return full_share(grid), weakest_dip(grid)


@pytest.fixture(params=[*PERIODIC, *SOLID], ids=[f'U+{ord(g):04X}' for g in [*PERIODIC, *SOLID]])
def glyph(request) -> str:
    return request.param


LEVELS: dict[tuple, tuple[float, float, tuple[float, float]]] = {}


@pytest.fixture
def levels(term, glyph) -> tuple[float, float, tuple[float, float]]:
    """(good, bad, subject) for this glyph in this engine, DPR and zoom, measured once per run."""
    key = (term.browser_name, term.dpr, term.zoom, glyph)
    if key not in LEVELS:
        LEVELS[key] = (
            measure(term, 'ov', glyph)[0],
            measure(term, 'base', glyph)[0],
            measure(term, 'term', glyph),
        )
    return LEVELS[key]


def test_lattice_tiles_across_cells(levels):
    """Mutation: a .term stack that paints the grid from the companion or a system fallback lands
    on the bad side of the learned margin; a mosaic fill without its overhang leaves a boundary
    column between full neighbours at the composite of two partial coverages."""
    good, bad, (subject, dip) = levels
    margin = (good + bad) / 2
    assert subject >= margin, (
        f'score {subject:.3f} below margin {margin:.3f} (good {good:.3f}, bad {bad:.3f})'
    )
    assert dip >= FULL, f'seam pixel at {dip:.3f}'


def test_companion_grid_fails_the_oracle(levels):
    """The bad fixture must land below the good one by a clear separation, or the margin above
    could not distinguish anything."""
    good, bad, _ = levels
    assert good - bad >= MIN_SEPARATION, f'good {good:.3f} bad {bad:.3f}'
