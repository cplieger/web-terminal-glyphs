"""The companion-tiles contract: `companion.TILES` equals what the companion face named in
`companion.SOURCE` tiles at this cell under the REACH rule. A companion release that moves a
glyph across the rule fails here rather than silently changing which font draws it.

The rule is per edge: left, right and top must be passed by our overhang (there the companion
meets its own kind and two partial coverages composite into a seam), the bottom by the frame alone
(there it meets ours, and our top overhang covers the boundary pixel). The second test pins the
premise of that bottom rule: nothing the companion tiles reaches the top edge, so whatever meets a
tiled glyph from below is drawn here.

Sits in the render tier because that is where MONASPACE_DIR is already required; it opens no
browser and runs once.
"""

from fontTools.pens.boundsPen import BoundsPen

from glyphs import cell, companion, families, table

EDGES = ('w', 's', 'e', 'n')
OVERHANG = (cell.LEFT_OVERHANG, cell.BOTTOM_OVERHANG, cell.RIGHT_OVERHANG, cell.TOP_OVERHANG)
INWARD = (1, 1, -1, -1)


def our_bounds(entry: table.Entry) -> tuple[float, float, float, float] | None:
    pen = BoundsPen(None)
    for contour in families.draw(entry):
        pen.moveTo(contour[0])
        for seg in contour[1:]:
            if len(seg) == 2:
                pen.lineTo(seg)
            else:
                pen.curveTo(seg[0:2], seg[2:4], seg[4:6])
        pen.closePath()
    return pen.bounds


def touched(entry: table.Entry) -> set[str]:
    """The cell edges our glyph reaches: those its ink overhangs, or all four for a pattern lattice,
    which spans the cell by rule and never overhangs."""
    if entry[0] == 'shade':
        return set(EDGES)
    bounds = our_bounds(entry)
    if bounds is None:
        return set()
    return {
        edge
        for edge, ours, limit, sign in zip(EDGES, bounds, OVERHANG, INWARD, strict=True)
        if sign * (ours - limit) <= 0
    }


def companion_tiles(font, cp: int, edges: set[str]) -> bool:
    glyph_set = font.getGlyphSet()
    pen = BoundsPen(glyph_set)
    glyph_set[font.getBestCmap()[cp]].draw(pen)
    if pen.bounds is None:
        return False
    return all(
        sign * (theirs - reach) <= 0
        for edge, theirs, reach, sign in zip(
            EDGES, pen.bounds, companion.REACH, INWARD, strict=True
        )
        if edge in edges
    )


def test_nothing_the_companion_tiles_reaches_the_top_edge():
    reaching = sorted(cp for cp in companion.TILES if 'n' in touched(table.CANDIDATES[cp]))
    assert reaching == [], [f'{cp:04X}' for cp in reaching]


def test_tiles_is_exactly_what_the_companion_tiles(companion_font):
    cmap = companion_font.getBestCmap()
    measured = {
        cp
        for cp, entry in table.CANDIDATES.items()
        if cp in cmap and companion_tiles(companion_font, cp, touched(entry))
    }
    extra = sorted(measured - companion.TILES)
    stale = sorted(companion.TILES - measured)
    assert (extra, stale) == ([], []), (
        f'companion tiles but TILES omits: {[f"{cp:04X}" for cp in extra]}; '
        f'TILES lists but the companion leaves a gap: {[f"{cp:04X}" for cp in stale]}'
    )
