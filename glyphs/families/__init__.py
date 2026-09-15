"""The six geometry families, and one entry point that draws a table entry with the right one."""

from typing import TYPE_CHECKING

from glyphs.families import dots, grid, shade, strokes, triangles
from glyphs.families import round as round_

if TYPE_CHECKING:
    from glyphs.contour import Contour
    from glyphs.table import Entry

FAMILIES = {
    'grid': grid,
    'dots': dots,
    'strokes': strokes,
    'triangles': triangles,
    'round': round_,
    'shade': shade,
}


def draw(entry: Entry) -> list[Contour]:
    family, params = entry
    return FAMILIES[family].draw(params)
