"""The shipped set is every candidate the companion cannot tile and has no better shape for:
`companion.LEFT_TO_COMPANION` names what is left to the companion, and the font, `cell.json` and
the generator table agree on it."""

from glyphs import companion, table


def test_every_companion_tiled_codepoint_is_absent_from_the_cmap(cmap):
    present = sorted(cp for cp in companion.TILES if cp in cmap)
    assert present == [], [f'{cp:04X}' for cp in present]


def test_tiles_only_name_codepoints_the_generator_knows():
    """A stale entry for a codepoint we never drew would exclude nothing and mean nothing."""
    unknown = sorted(companion.LEFT_TO_COMPANION - table.CANDIDATES.keys())
    assert unknown == [], [f'{cp:04X}' for cp in unknown]


def test_the_two_exclusion_sets_are_disjoint():
    """A codepoint in both would leave TILES unrecomputable from the companion's bounds."""
    both = sorted(companion.TILES & companion.NO_DESIGN_GAP)
    assert both == [], [f'{cp:04X}' for cp in both]


def test_cmap_is_the_candidates_minus_what_is_left_to_the_companion(cmap):
    assert set(cmap) == table.CANDIDATES.keys() - companion.LEFT_TO_COMPANION
    assert set(cmap) == set(table.TABLE)


def test_the_half_circles_are_the_companions_and_the_separators_are_ours(cmap):
    """Both directions: re-adding the text symbols fails here, and so does deleting the
    cell-spanning shape as unused."""
    for cp in (0x25D6, 0x25D7):
        assert cp not in cmap, f"U+{cp:04X} is the companion's: see companion.NO_DESIGN_GAP"
    for cp in (0xE0B4, 0xE0B5, 0xE0B6, 0xE0B7):
        assert cp in cmap, f'U+{cp:04X} is a Powerline separator and must stay ours'


def test_cell_json_states_the_rule(cell_json):
    assert cell_json['rule'].startswith('The overlay draws only what the companion cannot tile')
