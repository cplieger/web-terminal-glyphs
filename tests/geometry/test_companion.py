"""The shipped set is every candidate the companion cannot tile: `companion.TILES` names what is
left to the companion, and the font, `cell.json` and the generator table agree on it."""

from glyphs import companion, table


def test_every_companion_tiled_codepoint_is_absent_from_the_cmap(cmap):
    present = sorted(cp for cp in companion.TILES if cp in cmap)
    assert present == [], [f'{cp:04X}' for cp in present]


def test_tiles_only_name_codepoints_the_generator_knows():
    """A stale entry for a codepoint we never drew would exclude nothing and mean nothing."""
    unknown = sorted(companion.TILES - table.CANDIDATES.keys())
    assert unknown == [], [f'{cp:04X}' for cp in unknown]


def test_cmap_is_the_candidates_minus_the_tiles(cmap):
    assert set(cmap) == table.CANDIDATES.keys() - companion.TILES
    assert set(cmap) == set(table.TABLE)


def test_cell_json_states_the_rule(cell_json):
    assert cell_json['rule'].startswith('The overlay draws only what the companion cannot tile')
