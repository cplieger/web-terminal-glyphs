"""The codepoints the overlay leaves to the companion, because the companion's own glyph already
tiles at the cell: measured in the render tier, the pixel on every cell boundary it reaches is
painted solid by whatever meets it there.

A committed constant rather than a runtime read of the companion font, so the build is
reproducible from this repository alone and reads no outline of another font. The render tier's
`test_companion_tiles.py` recomputes the set from the companion named in SOURCE with the REACH
rule and fails when a companion release moves a glyph across it.

Measured on Monaspace Neon NF: its frame is x -10..1250, y -610..1900. Across the left, right
and top edges a companion glyph meets its own kind (a run of `─`, a row of `▄`, `│` under `│`),
and two partial coverages composite: a boundary column reads 0.81 of solid at DPR 1 and 0.43 at
DPR 2 zoom 1.1 where the glyph passes the edge by 10 units, and the top stops 29 units short of
the Gecko and WebKit row. Only a glyph passing the edge by our own overhang tiles there, and none
of the companion's do, so every side- or top-touching glyph stays ours. Across the bottom edge the
companion's glyph meets ours (whatever carries an upward arm touches the top, and is ours), and
our top overhang covers the boundary pixel alone: `╷` over `│` and `╻` over `┃` lose nothing in
48 legs (three engines, DPR 1 and 2, zoom 1.0 to 1.5), so the frame itself is enough there.
Result: 23 of the 197 codepoints the companion has tile at this cell, the 174 others do not.
"""

from glyphs import cell

# The cell in font units as the browsers frame it: x 0..1240; y is the union of the Gecko and
# WebKit row (baseline 13.5px, -500..1929) and the Blink row (baseline 13.0px, -571..1857).
FRAME = (0, -571, 1240, 1929)
# What a companion glyph's bound must pass, per edge (left, bottom, right, top), for that edge to
# tile: the frame by OVERHANG_UNITS where it meets its own kind, the frame alone at the bottom.
REACH = (
    FRAME[0] - cell.OVERHANG_UNITS,
    FRAME[1],
    FRAME[2] + cell.OVERHANG_UNITS,
    FRAME[3] + cell.OVERHANG_UNITS,
)
SOURCE = (
    'Monaspace Neon NF v1.400, MonaspaceNeonNF-Regular.woff2 '
    'sha256 8063ea45b6997c658035a4d876f996ecfa306c88fd0541d35d533fb1f9400c84'
)

TILES = frozenset(
    [
        # Box Drawing, 14: the double, triple and quadruple dashes, light and heavy, both axes,
        # and the two downward stubs, whose only edge is the bottom.
        0x2504,
        0x2505,
        0x2506,
        0x2507,
        0x2508,
        0x2509,
        0x250A,
        0x250B,
        0x254C,
        0x254D,
        0x254E,
        0x254F,
        0x2577,
        0x257B,
        # Geometric Shapes, 9: the three circles and the six arc spinners.
        0x25C9,
        0x25CB,
        0x25CF,
        0x25DC,
        0x25DD,
        0x25DE,
        0x25DF,
        0x25E0,
        0x25E1,
    ]
)


# Codepoints the companion draws at the right shape for their meaning, so the overlay draws
# nothing. Judged rather than measured, and kept out of TILES so that set stays recomputable from
# the companion's own bounds.
#
# U+25D6/25D7 are the halves of a black circle, and the overlay's only half-disc is `half_disc`,
# the Powerline separator: cell-spanning so it meets the block beside it, 1312x2573 units against
# the companion's 601x1212. U+E0B4..E0B7 keep it.
NO_DESIGN_GAP = frozenset([0x25D6, 0x25D7])

# The one set the generator subtracts.
LEFT_TO_COMPANION = TILES | NO_DESIGN_GAP
