GENERATED = [
    '2500-259F',
    '25C9',
    '25CB',
    '25CF',
    '25D6-25D7',
    '25DC-25E5',
    '2800-28FF',
    'E0B0-E0BF',
    'E0D6-E0D7',
    'EE00-EE0B',
    '1FB00-1FBAE',
    '1FBCE-1FBEF',
    '1CC1B-1CC3F',
    '1CD00-1CDE5',
    '1CE16-1CE19',
    '1CE51-1CEAF',
    'F5D0-F60D',
]


def expand(ranges: list[str]) -> set[int]:
    out: set[int] = set()
    for item in ranges:
        first, _, last = item.partition('-')
        out.update(range(int(first, 16), int(last or first, 16) + 1))
    return out


def test_cmap_is_exactly_the_generated_set(cmap):
    assert set(cmap) == expand(GENERATED)
    assert len(cmap) == 1098


def test_no_space_glyph(cmap):
    assert 0x20 not in cmap


def test_cell_json_generated_round_trips_to_the_cmap(cell_json, cmap):
    assert expand(cell_json['generated']) == set(cmap)
    assert cell_json['generated'] == GENERATED
