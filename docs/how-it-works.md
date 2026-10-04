# How web-terminal-glyphs works

This page explains why the glyphs come from a font and which codepoints it draws. It also covers how the font divides the work with Monaspace Neon NF and how the tests hold that division. Read it before you change a glyph, a range or the cell. Sizes on this page are in font units, 2000 to the em.

## Why the glyphs come from a font

A browser terminal renders each cell as a piece of text. So box-drawing lines, block elements, shades, braille and the Unicode mosaic blocks come from the font. A font does not know the cell it will be placed in. A text face draws these glyphs for its own line box, so at the cell a terminal actually uses they leave seams between rows. Patterned glyphs repeat at a pitch that does not divide the row height evenly. The ranges the face lacks fall back to a different font on each device.

Native terminals answer that by painting these ranges themselves. A DOM terminal cannot, because the painted pixels are also the text a user selects and copies.

web-terminal-glyphs is one small font holding only the glyphs that have to tile, generated from geometry for a declared cell. It is listed first in the `font-family` stack, so the browser takes those glyphs from here and everything else from the text face behind it. That face is the companion. The font carries no letters, no digits and no space, so the companion keeps its metrics, its line box and its look.

## The codepoint ranges

The set follows the glyphs [kitty](https://github.com/kovidgoyal/kitty) draws itself. These are the ranges the glyph tables know. The `generated` list in `cell.json` names the ranges the built font holds, after the codepoints left to the companion are taken out.

| Block | Codepoints |
| --- | --- |
| Box Drawing and Block Elements | `U+2500..U+259F` |
| Braille Patterns | `U+2800..U+28FF` |
| Symbols for Legacy Computing | `U+1FB00..U+1FBAE`, `U+1FBCE..U+1FBEF` |
| Legacy Computing Supplement, octants and separated blocks | `U+1CC1B..U+1CC3F`, `U+1CD00..U+1CDE5`, `U+1CE16..U+1CE19`, `U+1CE51..U+1CEAF` |
| Powerline arrows | `U+E0B0..U+E0BF`, `U+E0D6..U+E0D7` |
| Fira Code progress glyphs | `U+EE00..U+EE0B` |
| kitty branch-drawing glyphs | `U+F5D0..U+F60D` |
| Geometric Shapes | `U+25E2..U+25E5`, four triangles, plus eleven circles, arcs and half circles left to the companion |

Six geometry families cover them. They are grid fills, dot grids, stroke sets, triangles, rounded shapes and shades. Every glyph is drawn from a table entry, so a new range is a table change and a rebuild.

## What is left to the companion

The font draws only what the companion cannot tile at the declared cell, and nothing the companion already draws at the right shape. Of the 1,098 codepoints the tables know, Monaspace Neon NF lacks 901 and has 197.

Of those 197, 23 tile and are left to the companion with no entry in this font:

- The twelve box-drawing dashes, the three circles and the six arc spinners touch no cell edge.
- The two downward stubs `╷ ╻` touch only the bottom edge. Anything that inks the top edge from below is one of this font's glyphs and covers the seam. A glyph that inks nothing there leaves no seam to cover.

Two more, `◖ ◗`, are left to the companion for a different reason. They are the halves of a black circle. The only half-disc here is the Powerline separator, drawn to span the cell so it meets the block beside it. That is the right shape for `U+E0B4..U+E0B7`, which keep it, and the wrong one for a text symbol. This font's half-disc spans the cell at 1312 units wide, against the companion's 601.

## Why the other 172 are drawn here

The other 172 do not tile either, measured in the render tests. The companion's frame passes the left and right cell edges by 10 units and stops 29 units short of the top. So a run of its own `─` or `█` reads 0.81 of solid on every boundary column at device pixel ratio 1. At device pixel ratio 2 with page zoom 1.1 it reads 0.43.

This font's solid glyphs reach 72 units past each cell edge they touch, so every boundary pixel lies fully inside one neighbour.

## Where the two fonts meet

The glyphs that meet a companion glyph take its measured coordinates, so the join is flush. A `┼` of this font meets a `┄` of Monaspace's, so strokes, rails and arcs sit on Monaspace's stroke midline at y 645. They use its stroke widths of 160 and 400 units. The shades keep Monaspace's dot size and checkerboard phase, with the rows re-pitched to divide the cell.

Everything else keeps this font's own geometry. The half blocks and eighth bars split the cell evenly at its own centre, y 714.

The horizontal strokes and the shade dot rows carry `hstem` hints like Monaspace's. A hinted stem snaps to whole device pixel rows, so both fonts land a horizontal line on the same row.

## How the tests hold it

The set left to the companion is a committed constant in `glyphs/companion.py`, so the build reads no other font. The render tests recompute it from the companion file and fail when a Monaspace release moves a glyph across the rule.

The tests come in two tiers. `tests/geometry` checks the built outlines against the six geometry rules in `glyphs/cell.py`. `tests/render` renders a fixture page in Chromium, Firefox and WebKit and measures the pixels. It runs each engine at device pixel ratio 1 and 2 and page zoom 1.0 and 1.1. The seam tests learn their margin from two fixtures on the same page. This font alone is the good case and the companion alone the bad one.
