# web-terminal-glyphs

[![License](https://img.shields.io/github/license/cplieger/web-terminal-glyphs)](LICENSE)

> Terminal tiling glyphs drawn for one cell, as a web font that sits in front of your text face

A browser terminal renders each cell as a piece of text, so box-drawing lines,
block elements, shades, braille and the newer Unicode mosaic blocks come from
the font. A font does not know the cell it will be placed in, and the glyphs in
a text face are drawn for its own line box: at the cell a terminal actually
uses they leave seams between rows, lattices whose period does not divide the
row, and fallback substitutions per device for the ranges the face lacks.
Native terminals answer that by painting these ranges themselves. A DOM
terminal cannot, because the painted pixels are also the text a user selects
and copies.

`Web Terminal Glyphs` is the other answer: one small font holding only the
glyphs that have to tile, generated from geometry for a declared cell, and
listed first in the `font-family` stack so the browser takes them from here and
everything else from the text face behind it. It carries no letters, no digits
and no space, so the text face keeps its metrics, its line box and its look.

## Install

Fetch the release assets and serve them beside your text face:

```text
https://github.com/cplieger/web-terminal-glyphs/releases/latest/download/WebTerminalGlyphs.woff2
https://github.com/cplieger/web-terminal-glyphs/releases/latest/download/cell.json
https://github.com/cplieger/web-terminal-glyphs/releases/latest/download/LICENSE
```

Pin a release tag and a SHA-256 in an image build rather than `latest`;
the asset bytes never change under a tag.

**woff2 only, and no desktop format on purpose.** The outlines are drawn for one
cell, and a native terminal's cell is whatever its own font size and line height
produce, so an installed OTF would be subtly wrong at nearly every setting and
wrong in a way that reads as a font bug. The cell contract can only be honoured
where the cell is declared, which is a browser stylesheet.

## Usage

Declare the font once per weight and style you use, all pointing at the same
file, and put the family first in the stack of the element that renders cells:

```css
@font-face {
  font-family: "Web Terminal Glyphs";
  src: url("/vendor/fonts/WebTerminalGlyphs.woff2") format("woff2");
  font-weight: 400;
  font-style: normal;
  font-display: block;
}
/* repeat for 700/normal, 400/italic, 700/italic with the same src */

.term {
  font-family: "Web Terminal Glyphs", "Monaspace Neon NF", monospace;
  font-size: 14px;
  line-height: 17px;
  font-synthesis: none;
}
```

The four exact declarations keep every browser from synthesising a bold or an
oblique for the one upright design; box drawing must never slant or thicken.

## The cell contract

The glyphs are drawn for one cell and are wrong for any other. `cell.json`
states it:

| Field | Value | Meaning |
| --- | --- | --- |
| `companion.family` | `Monaspace Neon NF` | the text face the glyphs are paired with |
| `companion.advance` | 1240 / 2000 em | every glyph here has the same advance, so no cell is padded |
| `companion.ascender`, `descender`, `lineGap` | 1890 / −400 / 200 | copied into this font, because Gecko takes the line box from the first family in the stack |
| `cell.fontSize`, `cell.lineHeight` | 14 / 17 | the only ratio the glyphs tile at |
| `cell.overhang` | 72 units | how far a solid glyph extends past a cell edge so adjacent cells leave no seam |
| `generated` | 1,073 codepoints | the ranges this font answers for |
| `rule` | a sentence | what this font draws, and what it leaves to the companion |

Gate on it at build time: compare `cell.json` against the CSS you ship and
against the companion file you vendor. A companion release that changes its
advance or metrics, or a stylesheet that changes the cell, is a failing build,
not a visual regression discovered on a phone.

## What is generated

The set is the one [kitty](https://github.com/kovidgoyal/kitty) draws itself,
which is the most complete of the eleven terminals surveyed: Box Drawing and
Block Elements (U+2500–259F), Braille (U+2800–28FF), Symbols for Legacy
Computing (U+1FB00–1FBAE, U+1FBCE–1FBEF), the Legacy Computing Supplement's
octants and separated blocks (U+1CC1B–1CC3F, U+1CD00–1CDE5, U+1CE16–1CE19,
U+1CE51–1CEAF), Powerline arrows (U+E0B0–E0BF, U+E0D6–E0D7), Fira Code's
progress glyphs (U+EE00–EE0B), kitty's branch-drawing glyphs (U+F5D0–F60D)
and a handful of Geometric Shapes.

Six geometry families cover it: grid fills, dot grids, stroke sets, triangles,
rounded shapes and shades. Every glyph is drawn from a table entry, so a new
range is a table change and a rebuild.

The overlay draws only what the companion cannot tile at the declared cell, and
nothing the companion already draws at the right shape. Of the 1,098 codepoints
the tables know, Monaspace Neon NF lacks 901; of the 197 it has, 23 tile and are
left to the companion with no entry in this font: the
twelve box-drawing dashes, the three circles and the six arc spinners touch no
cell edge, and the two downward stubs `╷ ╻` touch only the bottom edge, where
anything that inks the top edge from below is one of ours and covers the seam
(a glyph that inks nothing there leaves no seam to cover). Two more are left to
it for a different reason: `◖ ◗` are the halves of a black circle, and the only
half-disc here is the Powerline separator, drawn to span the cell so it meets the
block beside it: the right shape for `U+E0B4`..`U+E0B7`, which keep it, and the
wrong one for a text symbol, since ours spans the cell at 1312 units against the
companion's 601. The other 172 do not tile either, measured: the companion's
frame passes the left and right cell edges by 10 units and stops 29 short of the
top, so a run of its own `─` or `█` reads 0.81 of solid on every boundary column
at DPR 1 and 0.43 at DPR 2 zoom 1.1. Those are drawn here. The ones that meet a
companion glyph take its measured
coordinates so the join is flush: strokes, rails and arcs sit on Monaspace's
stroke midline (y 645) at its stroke widths, because a `┼` of ours meets a `┄`
of Monaspace's; the shades keep its dot size and checkerboard phase with the
rows re-pitched to divide the cell. Everything else keeps this font's own
geometry (the half blocks and eighth bars split the cell evenly at its lattice
centre, y 714). The horizontal strokes and shade dot rows carry `hstem` hints
like Monaspace's, so both fonts snap to the same device rows. The set is a
committed constant in `glyphs/companion.py`; the render tier recomputes it from
the companion file and fails when a companion release moves a glyph across the
rule.

## Building

```sh
uv run scripts/build.py          # dist/WebTerminalGlyphs.woff2, cell.json, LICENSE, NOTICE
uv run pytest tests/geometry     # invariants on the built font
uv run pytest tests/render       # Chromium, Firefox and WebKit through Playwright
```

The build needs Python 3.14 or newer: the glyph table derives the Legacy
Computing Supplement entries from `unicodedata` names, and those exist from
Unicode 16.0, which is the database Python 3.14 ships (3.13 carries 15.1).

The render tests need `uv run playwright install chromium firefox webkit`
once, and the companion face to pair against: set `MONASPACE_DIR` to a
directory holding the four `MonaspaceNeonNF-{Regular,Bold,Italic,BoldItalic}.woff2`
files from a [Monaspace release](https://github.com/githubnext/monaspace/releases).
The session copies them into `tests/fixtures/base/` on start and deletes
the copy on exit; the repository never commits Monaspace, and the build
never reads it.

## Related projects

- [web-terminal-engine](https://github.com/cplieger/web-terminal-engine): the
  VT engine and wire protocol whose renderer these glyphs are drawn for.
- [web-terminal-ui](https://github.com/cplieger/web-terminal-ui): the browser
  UI that declares the cell and ships the stylesheet this font pairs with.
- [Monaspace](https://github.com/githubnext/monaspace): the companion text
  face, consumed unmodified.

## Contributing

See [CONTRIBUTING](https://github.com/cplieger/.github/blob/main/CONTRIBUTING.md).

## Disclaimer

This project is built with care and follows security best practices, but it is intended for personal / self-hosted use. No guarantees of fitness for production environments. Use at your own risk.

This project was built with AI-assisted tooling using [Claude](https://claude.com), [GPT](https://openai.com), and [Kiro](https://kiro.dev). The human maintainer defines architecture, supervises implementation, and makes all final decisions.

## License

[Apache-2.0](LICENSE), the font file included. The glyph outlines are
generated from this repository's own geometry tables; nothing of the companion
face is copied into the font. Monaspace is consumed unmodified under its own
[SIL Open Font License 1.1](https://github.com/githubnext/monaspace/blob/main/LICENSE).
