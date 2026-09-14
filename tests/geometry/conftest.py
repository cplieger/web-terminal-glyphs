"""Fixtures over the BUILT font. GLYPHS_FONT points the suite at another font file (the red check
against the companion), GLYPHS_DIST at another build directory."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
DIST = Path(os.environ.get('GLYPHS_DIST', ROOT / 'dist'))


@pytest.fixture(scope='session')
def font_path() -> Path:
    if 'GLYPHS_FONT' in os.environ:
        return Path(os.environ['GLYPHS_FONT'])
    path = DIST / 'WebTerminalGlyphs.woff2'
    if not path.exists():
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'build.py'), str(DIST)], check=True)
    return path


@pytest.fixture(scope='session')
def font(font_path: Path) -> TTFont:
    return TTFont(font_path)


@pytest.fixture(scope='session')
def cmap(font: TTFont) -> dict[int, str]:
    return font.getBestCmap()


@pytest.fixture(scope='session')
def bounds(font: TTFont, cmap: dict[int, str]):
    glyph_set = font.getGlyphSet()

    def of(codepoint: int) -> tuple[int, int, int, int]:
        pen = BoundsPen(glyph_set)
        glyph_set[cmap[codepoint]].draw(pen)
        assert pen.bounds is not None, f'U+{codepoint:04X} has no ink'
        return tuple(round(v) for v in pen.bounds)

    return of


@pytest.fixture(scope='session')
def contour_boxes(font: TTFont, cmap: dict[int, str]):
    """Bounding boxes of a glyph's separate contours, from their on-curve points, sorted."""
    glyph_set = font.getGlyphSet()

    def of(codepoint: int) -> list[tuple[int, int, int, int]]:
        pen = RecordingPen()
        glyph_set[cmap[codepoint]].draw(pen)
        boxes, current = [], []
        for op, args in pen.value:
            if op in ('moveTo', 'lineTo', 'curveTo'):
                current.append(args[-1])
            elif op == 'closePath' and current:
                xs, ys = [p[0] for p in current], [p[1] for p in current]
                boxes.append((min(xs), min(ys), max(xs), max(ys)))
                current = []
        return sorted(boxes)

    return of


@pytest.fixture(scope='session')
def cell_json() -> dict:
    return json.loads((DIST / 'cell.json').read_text())
