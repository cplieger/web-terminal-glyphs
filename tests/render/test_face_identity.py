"""Oracle (a) face identity and (e) Latin untouched.

Chromium answers through CDP `CSS.getPlatformFontsForNode`; Firefox and WebKit compare a DOM
screenshot of the same span rendered under .term and under .base.
"""

OVERLAY = 'Web Terminal Glyphs'
COMPANION = 'Monaspace Krypton Var'
# One glyph per generated range, in the design's order.
SAMPLES = [
    '\u2500',
    '\u250c',
    '\u2550',
    '\u2578',
    '\u257c',
    '\u25d6',
    '\u25e2',
    '\u28ff',
    '\ue0b0',
    '\ue0d6',
    '\uee00',
    '\U0001fb00',
    '\U0001fbce',
    '\U0001cc1b',
    '\U0001cd00',
    '\U0001ce16',
    '\U0001ce51',
    '\uf5d0',
]
# One codepoint the companion tiles per group it tiles in: a light and a heavy dash, a double dash,
# a downward stub, a white circle and an arc spinner.
DROPPED = ['\u2504', '\u2509', '\u254c', '\u2577', '\u25cb', '\u25dc']


def span(index: int) -> str:
    return f'#block .row span:nth-child({index + 1})'


def test_overlay_paints_every_generated_range(term):
    """Mutation: a .term stack without the overlay family paints these from the companion or a
    system fallback, so Chromium names another family and the .term/.base screenshots agree."""
    term.set_rows('term', [SAMPLES])
    if term.browser_name == 'chromium':
        for i, sample in enumerate(SAMPLES):
            assert term.fonts(span(i)) == [OVERLAY], (sample, term.fonts(span(i)))
        return
    with_overlay = [term.png(span(i)) for i in range(len(SAMPLES))]
    term.set_rows('base', [SAMPLES])
    for i, sample in enumerate(SAMPLES):
        assert with_overlay[i] != term.png(span(i)), (
            f'U+{ord(sample):04X} renders the same without the overlay'
        )


def test_companion_paints_every_dropped_range(term):
    """Mutation: an overlay that still carried a companion-tiled codepoint would win the cell,
    moving Chromium's answer to the overlay and changing the .term screenshot against .base."""
    term.set_rows('term', [DROPPED])
    if term.browser_name == 'chromium':
        for i, sample in enumerate(DROPPED):
            assert term.fonts(span(i)) == [COMPANION], (sample, term.fonts(span(i)))
        return
    with_overlay = [term.png(span(i)) for i in range(len(DROPPED))]
    term.set_rows('base', [DROPPED])
    for i, sample in enumerate(DROPPED):
        assert with_overlay[i] == term.png(span(i)), (
            f'U+{ord(sample):04X} renders differently with the overlay in the stack'
        )


def test_latin_and_space_come_from_the_companion(term):
    """Mutation: an overlay that carried U+0020 or Latin would win these cells, moving Chromium's
    answer to the overlay and changing the .term screenshot of 'Mi' against .base."""
    term.set_rows('term', [['M', 'i', ' ', 'Mi']])
    if term.browser_name == 'chromium':
        for i in range(3):
            assert term.fonts(span(i)) == [COMPANION], term.fonts(span(i))
        return
    with_overlay = term.png(span(3))
    term.set_rows('base', [['M', 'i', ' ', 'Mi']])
    assert with_overlay == term.png(span(3))
