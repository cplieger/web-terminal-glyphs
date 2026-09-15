#!/usr/bin/env python3
"""Build dist/WebTerminalGlyphs.woff2, cell.json, LICENSE and NOTICE from the geometry table.

Usage: uv run scripts/build.py [dist_dir]
"""

import json
import sys
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.misc.timeTools import timestampFromString
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from glyphs import cell, families, table
from glyphs.families import shade

ROOT = Path(__file__).resolve().parent.parent
FONT_FILE = 'WebTerminalGlyphs.woff2'
NOTICE = (
    'Web Terminal Glyphs\n'
    f'{cell.COPYRIGHT}\n\n'
    "Generated from this repository's geometry tables. Contains no glyph outlines from any other font.\n"
)
USE_TYPO_METRICS = 1 << 7
BUILD_TIMESTAMP = timestampFromString('Thu Jan  1 00:00:00 2026')
REGULAR = 1 << 6


def glyph_name(cp: int) -> str:
    return f'uni{cp:04X}' if cp < 0x10000 else f'u{cp:04X}'


STROKE_HEIGHTS = frozenset(cell.STROKE_UNITS.values())
SHADE_DOT_HEIGHTS = frozenset(kind.dot[1] for kind in shade.KINDS.values())


def stem_heights(entry: table.Entry) -> frozenset[int]:
    """The rectangle heights that are horizontal stems in this glyph: a stroke width in any glyph,
    a dot row in the shade dithers. Nothing else is hinted: the engine hints only the vertical
    direction, and a block edge is left where it is (measured on `▀` beside `▄`)."""
    return STROKE_HEIGHTS | SHADE_DOT_HEIGHTS if entry[0] == 'shade' else STROKE_HEIGHTS


def hstems(contours, heights: frozenset[int]) -> list[tuple[int, int]]:
    """Non-overlapping (bottom, height) horizontal stem hints, one per rectangle of a stem height.
    The companion's box-drawing glyphs carry the same hints, and FreeType's CFF engine snaps a
    hinted stem's edges to the device rows, so without them a junction's arm lands up to half a
    row off the companion's dash at a fractional zoom. A heavy arm's stem contains a light arm's
    on a mixed-weight junction; nested or overlapping spans are merged because Type 2 allows
    overlap only under a hintmask."""
    spans = set()
    for contour in contours:
        if len(contour) != 4 or any(len(seg) != 2 for seg in contour):
            continue
        xs, ys = {p[0] for p in contour}, {p[1] for p in contour}
        if len(xs) == 2 and len(ys) == 2 and max(ys) - min(ys) in heights:
            spans.add((min(ys), max(ys)))
    merged: list[list[int]] = []
    for lo, hi in sorted(spans):
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return [(lo, hi - lo) for lo, hi in merged]


def hint_program(contours, heights: frozenset[int]) -> list:
    """`hstem` with the deltas Type 2 wants: each stem's bottom relative to the previous top."""
    pos = 0
    args: list[int] = []
    for bottom, height in hstems(contours, heights):
        args += [bottom - pos, height]
        pos = bottom + height
    return [*args, 'hstem'] if args else []


def charstring(contours, heights: frozenset[int] = STROKE_HEIGHTS):
    pen = T2CharStringPen(width=cell.ADVANCE_UNITS, glyphSet=None)
    for contour in contours:
        pen.moveTo(contour[0])
        for seg in contour[1:]:
            if len(seg) == 2:
                pen.lineTo(seg)
            else:
                pen.curveTo(seg[0:2], seg[2:4], seg[4:6])
        pen.closePath()
    cs = pen.getCharString()
    cs.program[1:1] = hint_program(contours, heights)
    return cs


def ink_bounds(glyph_bounds) -> tuple[int, int, int, int]:
    inked = [b for b in glyph_bounds if b]
    return (
        round(min(b[0] for b in inked)),
        round(min(b[1] for b in inked)),
        round(max(b[2] for b in inked)),
        round(max(b[3] for b in inked)),
    )


def glyph_bounds(font: TTFont) -> dict[str, tuple[int, int, int, int] | None]:
    glyph_set = font.getGlyphSet()
    out = {}
    for name in glyph_set:
        pen = BoundsPen(glyph_set)
        glyph_set[name].draw(pen)
        out[name] = pen.bounds and tuple(round(v) for v in pen.bounds)
    return out


def build_font() -> tuple[FontBuilder, tuple[int, int, int, int]]:
    codepoints = sorted(table.TABLE)
    names = {cp: glyph_name(cp) for cp in codepoints}
    charstrings = {'.notdef': charstring([])}
    for cp in codepoints:
        entry = table.TABLE[cp]
        charstrings[names[cp]] = charstring(families.draw(entry), stem_heights(entry))

    fb = FontBuilder(unitsPerEm=cell.UPEM, isTTF=False)
    fb.setupGlyphOrder(['.notdef', *names.values()])
    fb.setupCharacterMap({cp: names[cp] for cp in codepoints})
    fb.setupCFF(
        cell.POSTSCRIPT_NAME,
        {
            'FullName': cell.FAMILY_NAME,
            'FamilyName': cell.FAMILY_NAME,
            'Weight': 'Regular',
            'version': cell.VERSION,
            'Notice': cell.COPYRIGHT,
        },
        charstrings,
        {},
    )
    # calcBounds needs the Private dict setupCFF attaches to each charstring.
    per_glyph = {name: cs.calcBounds(None) for name, cs in charstrings.items()}
    fb.setupHorizontalMetrics(
        {name: (cell.ADVANCE_UNITS, round(b[0]) if b else 0) for name, b in per_glyph.items()}
    )
    bounds = ink_bounds(per_glyph.values())
    fb.setupHorizontalHeader(
        ascent=cell.COMPANION_ASCENDER_UNITS,
        descent=cell.COMPANION_DESCENDER_UNITS,
        lineGap=cell.COMPANION_LINE_GAP_UNITS,
    )
    fb.setupNameTable(
        {
            'copyright': cell.COPYRIGHT,
            'familyName': cell.FAMILY_NAME,
            'styleName': 'Regular',
            'uniqueFontIdentifier': f'{cell.VERSION};{cell.POSTSCRIPT_NAME}',
            'fullName': cell.FAMILY_NAME,
            'version': f'Version {cell.VERSION}',
            'psName': cell.POSTSCRIPT_NAME,
            'licenseDescription': cell.LICENSE_ID,
            'licenseInfoURL': cell.LICENSE_URL,
        }
    )
    fb.setupOS2(
        version=4,
        sTypoAscender=cell.COMPANION_ASCENDER_UNITS,
        sTypoDescender=cell.COMPANION_DESCENDER_UNITS,
        sTypoLineGap=cell.COMPANION_LINE_GAP_UNITS,
        usWinAscent=bounds[3],
        usWinDescent=-bounds[1],
        fsSelection=USE_TYPO_METRICS | REGULAR,
        fsType=0,
        achVendID='CPLG',
    )
    fb.setupPost()
    fb.updateHead(
        fontRevision=float(cell.VERSION),
        created=BUILD_TIMESTAMP,
        modified=BUILD_TIMESTAMP,
        xMin=bounds[0],
        yMin=bounds[1],
        xMax=bounds[2],
        yMax=bounds[3],
    )
    return fb, bounds


def verify(path: Path, expected_glyphs: int) -> None:
    font = TTFont(path)
    cmap = font.getBestCmap()
    if len(cmap) != expected_glyphs or 0x20 in cmap:
        raise SystemExit(f'cmap has {len(cmap)} entries, expected {expected_glyphs} without U+0020')
    wrong = [
        name for name, (advance, _) in font['hmtx'].metrics.items() if advance != cell.ADVANCE_UNITS
    ]
    if wrong:
        raise SystemExit(f'advance is not {cell.ADVANCE_UNITS} on {wrong[:5]}')
    bearings = [
        name
        for name, bounds in glyph_bounds(font).items()
        if font['hmtx'].metrics[name][1] != (bounds[0] if bounds else 0)
    ]
    if bearings:
        raise SystemExit(f'left side bearing is not the ink xMin on {bearings[:5]}')
    if font['hhea'].ascent != font['OS/2'].sTypoAscender:
        raise SystemExit('hhea.ascender differs from OS/2.sTypoAscender')
    if font['head'].unitsPerEm != cell.UPEM:
        raise SystemExit(f'unitsPerEm is {font["head"].unitsPerEm}, expected {cell.UPEM}')


def write_cell_json(path: Path) -> None:
    data = {
        'family': cell.FAMILY_NAME,
        'companion': {
            'family': cell.COMPANION_FAMILY,
            'unitsPerEm': cell.UPEM,
            'advance': cell.ADVANCE_UNITS,
            'ascender': cell.COMPANION_ASCENDER_UNITS,
            'descender': cell.COMPANION_DESCENDER_UNITS,
            'lineGap': cell.COMPANION_LINE_GAP_UNITS,
        },
        'cell': {
            'fontSize': cell.CELL_FONT_SIZE_PX,
            'lineHeight': cell.CELL_LINE_HEIGHT_PX,
            'ratio': round(cell.CELL_RATIO, 7),
            'baseline': cell.CELL_BASELINE_PX,
            'top': cell.TOP_UNITS,
            'bottom': cell.BOTTOM_UNITS,
            'overhang': cell.OVERHANG_UNITS,
        },
        'stack': [cell.FAMILY_NAME, cell.COMPANION_FAMILY],
        'rule': (
            'The overlay draws only what the companion cannot tile at this cell; every other '
            'codepoint falls through to the companion.'
        ),
        'generated': table.generated_ranges(),
    }
    path.write_text(json.dumps(data, indent=2) + '\n')


def main() -> None:
    dist = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'dist'
    dist.mkdir(parents=True, exist_ok=True)
    fb, bounds = build_font()
    fb.font.flavor = 'woff2'
    font_path = dist / FONT_FILE
    fb.save(font_path)
    verify(font_path, len(table.TABLE))
    write_cell_json(dist / 'cell.json')
    root_license = ROOT / 'LICENSE'
    if root_license.exists():
        (dist / 'LICENSE').write_bytes(root_license.read_bytes())
    else:
        print('warning: no LICENSE at the repo root; writing a placeholder', file=sys.stderr)
        (dist / 'LICENSE').write_text(f'{cell.LICENSE_ID}: {cell.LICENSE_URL}\n')
    (dist / 'NOTICE').write_text(NOTICE)
    print(
        f'{len(table.TABLE)} glyphs, {font_path.stat().st_size} bytes, ink bounds x [{bounds[0]}, {bounds[2]}] y [{bounds[1]}, {bounds[3]}]'
    )


if __name__ == '__main__':
    main()
