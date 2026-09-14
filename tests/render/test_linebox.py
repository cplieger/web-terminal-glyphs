"""Oracle (d) line box: with the overlay first in the stack, baseline offset, span height and row
height equal the companion-only row for Latin-only, overlay-only and mixed rows."""

import pytest

EXPECTED_BASELINE_PX = {'chromium': 13.0, 'firefox': 13.5, 'webkit': 13.5}
ROWS = {'latin': 'Mi', 'overlay': '░█', 'mixed': '░█Mi'}


@pytest.mark.parametrize('content', list(ROWS), ids=list(ROWS))
def test_line_box_equals_the_companion_only_row(term, content):
    """Mutation: an overlay whose ascender is 60 units (about half a pixel at 14px) or more off the
    companion's moves the baseline and the span height in every engine, Latin-only rows included,
    because the line box comes from the first family in the stack."""
    term.set_rows('base', [[ROWS['mixed']]])
    base = term.probe(0)
    term.set_rows('term', [[ROWS[content]]])
    assert term.probe(0) == base


def test_companion_row_has_the_measured_line_box(term):
    term.set_rows('base', [[ROWS['mixed']]])
    probe = term.probe(0)
    if term.zoom == 1.0:
        assert (probe['baseline'], probe['rowHeight']) == (
            EXPECTED_BASELINE_PX[term.browser_name],
            17,
        )
    assert probe['spanHeight'] < probe['rowHeight']
