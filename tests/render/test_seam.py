"""Oracle (b) seam, on a 6 x 6 grid of one glyph per lattice family, with a margin learned per run
from two fixtures rendered in the same page: the overlay alone (good) and the companion alone
(bad); the subject is the production .term stack.

The braille lattice scores the correlation of the grid with itself shifted by the glyph's own
period, on the weaker of the two axes: a pattern that continues across cells scores near 1, one
whose period does not divide the cell drops at every seam. The three shades left this test when
they took the companion's one-pixel dots: a correlation at a fractional lag interpolates a
1 px dot into noise and reads the same for a lattice that tiles and one that does not (measured
0.756 against 0.757 for the light shade at DPR 2); `test_shade.py` measures them another way. Mosaic fills
(octant 2345678, sextant 23456) tile into a solid field with one notch per cell; they score the
share of the grid at the run's own `ink_floor`, and a seam is the extra check: a pixel below that
floor between two neighbours above it, which is what a boundary column at two partial coverages
looks like. The floor was an absolute 254/255, which held here and failed on the ubuntu-24.04
runner, where a correct build reads 250/255 at the boundary.
"""

import pytest

from tests.render import pixels

UNIT_PX = 14 / 2000
# Own period (vertical, horizontal) in font units: the octant pitch 607 x 620.
PERIODIC = {'\u28ff': (607, 620)}
SOLID = ['\U0001cde5', '\U0001fb3b']
GRID = 6
# Smallest separation measured across the three engines at DPR 1 and 2, zoom 1.0 and 1.1: 0.07,
# the dark shade in WebKit at DPR 2, where the companion's period is only 8% off the cell.
MIN_SEPARATION = 0.05


def periodicity(grid: list[list[float]], own_units: tuple[float, float], scale: float) -> float:
    own_v, own_h = own_units[0] * UNIT_PX * scale, own_units[1] * UNIT_PX * scale
    return min(
        pixels.correlation(grid, own_v, vertical=True),
        pixels.correlation(grid, own_h, vertical=False),
    )


def full_share(grid: list[list[float]], floor: float) -> float:
    return sum(v >= floor for row in grid for v in row) / (len(grid) * len(grid[0]))


def weakest_dip(grid: list[list[float]], floor: float) -> tuple[float, int, int] | None:
    """The weakest pixel below `floor` that sits between two neighbours at or above it, along
    either axis; None when no such pixel exists."""
    dips = [
        (grid[y][x], y, x)
        for y in range(1, len(grid) - 1)
        for x in range(1, len(grid[y]) - 1)
        if grid[y][x] < floor
        and (
            (grid[y][x - 1] >= floor and grid[y][x + 1] >= floor)
            or (grid[y - 1][x] >= floor and grid[y + 1][x] >= floor)
        )
    ]
    return min(dips) if dips else None


def measure(term, cls: str, glyph: str, floor: float) -> tuple[float, str | None]:
    """(score for the learned margin, seam report or None) of the 6 x 6 grid under `cls`. The
    report is built here, while the page still holds the rows it describes."""
    term.set_rows(cls, [[glyph * GRID]] * GRID)
    grid = pixels.crop_to_ink(term.ink('#block'))
    if glyph in PERIODIC:
        return periodicity(grid, PERIODIC[glyph], term.scale), None
    seam = weakest_dip(grid, floor)
    report = None if seam is None else term.diagnose(grid, *seam[1:], floor, '#block .row span')
    return full_share(grid, floor), report


@pytest.fixture(params=[*PERIODIC, *SOLID], ids=[f'U+{ord(g):04X}' for g in [*PERIODIC, *SOLID]])
def glyph(request) -> str:
    return request.param


LEVELS: dict[tuple, tuple[float, float, tuple[float, str | None]]] = {}


@pytest.fixture
def levels(term, glyph, ink_floor) -> tuple[float, float, tuple[float, str | None]]:
    """(good, bad, subject) for this glyph in this engine, DPR and zoom, measured once per run."""
    key = (term.browser_name, term.dpr, term.zoom, glyph)
    if key not in LEVELS:
        LEVELS[key] = (
            measure(term, 'ov', glyph, ink_floor)[0],
            measure(term, 'base', glyph, ink_floor)[0],
            measure(term, 'term', glyph, ink_floor),
        )
    return LEVELS[key]


def test_lattice_tiles_across_cells(levels):
    """Mutation: a .term stack that paints the grid from the companion or a system fallback lands
    on the bad side of the learned margin; a mosaic fill without its overhang leaves a boundary
    column between full neighbours at the composite of two partial coverages."""
    good, bad, (subject, seam) = levels
    margin = (good + bad) / 2
    assert subject >= margin, (
        f'score {subject:.3f} below margin {margin:.3f} (good {good:.3f}, bad {bad:.3f})'
    )
    assert seam is None, seam


def test_companion_grid_fails_the_oracle(levels):
    """The bad fixture must land below the good one by a clear separation, or the margin above
    could not distinguish anything."""
    good, bad, _ = levels
    assert good - bad >= MIN_SEPARATION, f'good {good:.3f} bad {bad:.3f}'
