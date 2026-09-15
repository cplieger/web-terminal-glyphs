"""Oracle (b) for the three shades: a 3 x 3 block shows no band at the cell pitch in the vertical
axis, with the margin learned per run from the overlay alone (good) and the companion alone (bad).

The statistic is the largest change between the block's per-row mean ink and itself one period of
the lattice further on (four rows of the light and dark shade, half the cell; two rows of the
medium): a lattice whose rows continue across the seam at their interior pitch reads near 0, the
companion's shades (rows 311 or 178 units apart in a 2428-unit row, so the pitch across a seam is
60 units shorter) read the seam. The vertical axis only: the companion's shades already
tile horizontally at this cell (the audit finds its column pitch continues to within one unit), so
there is no bad pole for a column band, and the geometry tier pins our columns.

DPR 2 at zoom 1.0 only, on measurement, because a test that cannot fail must not exist. At DPR 1
the rasterizer snaps both lattices' eight rows onto the same 17 device rows (the light shade's row
profile is identical for the two fonts to the second decimal), and at zoom 1.1 the fractional cell
and the fractional lag interpolate the one-pixel dots into noise; in those six legs the good and
bad poles come out level, separated by 0.001 to 0.06 with the sign flipping between engines and
shades, so an oracle placed there could not tell the tiling build from the companion and could
never fail. At DPR 2, zoom 1.0 every engine separates the poles by 0.14 or more, and
`test_companion_shade_fails_the_oracle` keeps that separation a measured precondition. The
DPR-independent half of the claim, that the dot pitch across a cell seam equals the pitch inside
the cell, is pinned in the geometry tier (`test_lattice.py`).
"""

import pytest

from tests.render import pixels
from tests.render.test_seam import MIN_SEPARATION, UNIT_PX

# Vertical period in font units: four of the light and dark shade's eight rows, two of the
# medium's fourteen.
PERIOD = {'\u2591': 1214, '\u2592': 2428 / 7, '\u2593': 1214}
BLOCK = 3


@pytest.fixture(params=[2], ids=['dpr2'])
def dpr(request) -> int:
    return request.param


@pytest.fixture(params=[1.0], ids=['zoom1.0'])
def zoom(request) -> float:
    return request.param


@pytest.fixture(params=list(PERIOD), ids=[f'U+{ord(g):04X}' for g in PERIOD])
def shade(request) -> str:
    return request.param


def row_profile(grid: list[list[float]]) -> list[float]:
    return [sum(row) / len(row) for row in grid]


def band(profile: list[float], period: float) -> float:
    """The largest change between the profile and itself `period` device pixels (fractional,
    linear interpolation) further on."""
    n, f = int(period), period - int(period)
    return max(
        (
            abs(profile[i] - (1 - f) * profile[i + n] - f * profile[i + n + 1])
            for i in range(len(profile) - n - 1)
        ),
        default=0.0,
    )


def band_score(term, cls: str, glyph: str) -> float:
    term.set_rows(cls, [[glyph * BLOCK]] * BLOCK)
    rows = row_profile(pixels.crop_to_ink(term.ink('#block')))
    return 1 - band(rows, PERIOD[glyph] * UNIT_PX * term.scale)


LEVELS: dict[tuple, tuple[float, float, float]] = {}


@pytest.fixture
def levels(term, shade) -> tuple[float, float, float]:
    key = (term.browser_name, term.dpr, term.zoom, shade)
    if key not in LEVELS:
        LEVELS[key] = (
            band_score(term, 'ov', shade),
            band_score(term, 'base', shade),
            band_score(term, 'term', shade),
        )
    return LEVELS[key]


def test_shade_block_has_no_cell_pitch_band(levels):
    """Mutation: a .term stack that paints the shades from the companion lands on the bad side."""
    good, bad, subject = levels
    margin = (good + bad) / 2
    assert subject >= margin, (
        f'score {subject:.3f} below margin {margin:.3f} (good {good:.3f}, bad {bad:.3f})'
    )


def test_companion_shade_fails_the_oracle(levels):
    good, bad, _ = levels
    assert good - bad >= MIN_SEPARATION, f'good {good:.3f} bad {bad:.3f}'
