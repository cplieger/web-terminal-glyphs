import pytest

FAMILY = 'Web Terminal Glyphs'
POSTSCRIPT = 'WebTerminalGlyphs-Regular'
LICENSE = 'Apache-2.0'
LICENSE_URL = 'https://www.apache.org/licenses/LICENSE-2.0'
FOREIGN = ('Monaspace', 'Neon', 'Argon', 'Xenon', 'Radon', 'Krypton')


def records(font, name_id: int) -> set[str]:
    return {record.toUnicode() for record in font['name'].names if record.nameID == name_id}


@pytest.mark.parametrize(
    ('name_id', 'expected'),
    [(1, FAMILY), (2, 'Regular'), (4, FAMILY), (6, POSTSCRIPT), (13, LICENSE), (14, LICENSE_URL)],
)
def test_name_record(font, name_id, expected):
    assert records(font, name_id) == {expected}


def test_copyright(font):
    assert records(font, 0) == {'Copyright 2026 cplieger'}


def test_no_companion_name_anywhere(font):
    for record in font['name'].names:
        text = record.toUnicode()
        assert not any(word in text for word in FOREIGN), (record.nameID, text)
