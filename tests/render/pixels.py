"""Decode Playwright's PNG screenshots with the standard library and measure them."""

import struct
import zlib

Image = list[list[tuple[int, int, int, int]]]


def decode(data: bytes) -> Image:
    """RGBA rows of an 8-bit RGB or RGBA non-interlaced PNG."""
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos, idat, width, height, channels = 8, b'', 0, 0, 0
    while pos < len(data):
        (length,), kind = struct.unpack('>I', data[pos : pos + 4]), data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        if kind == b'IHDR':
            width, height, depth, colour, _, _, interlace = struct.unpack('>IIBBBBB', body)
            assert depth == 8, depth
            assert interlace == 0, interlace
            channels = {2: 3, 6: 4}[colour]
        elif kind == b'IDAT':
            idat += body
        pos += 12 + length
    raw = zlib.decompress(idat)
    stride = width * channels
    rows: list[bytearray] = []
    prev = bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        filter_type, line = raw[start], bytearray(raw[start + 1 : start + 1 + stride])
        _unfilter(filter_type, line, prev, channels)
        rows.append(line)
        prev = line
    return [
        [
            (row[i], row[i + 1], row[i + 2], row[i + 3] if channels == 4 else 255)
            for i in range(0, stride, channels)
        ]
        for row in rows
    ]


def _unfilter(filter_type: int, line: bytearray, prev: bytearray, bpp: int) -> None:
    for i in range(len(line)):
        a = line[i - bpp] if i >= bpp else 0
        b = prev[i]
        c = prev[i - bpp] if i >= bpp else 0
        if filter_type == 1:
            line[i] = (line[i] + a) & 0xFF
        elif filter_type == 2:
            line[i] = (line[i] + b) & 0xFF
        elif filter_type == 3:
            line[i] = (line[i] + (a + b) // 2) & 0xFF
        elif filter_type == 4:
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 0xFF


def ink(image: Image) -> list[list[float]]:
    """Grey level 0..1 per pixel, the weakest colour channel, so "full ink" means every channel
    is within 1/255 of the glyph colour."""
    return [[min(r, g, b) / 255 for r, g, b, _ in row] for row in image]


def correlation(grid: list[list[float]], lag: float, *, vertical: bool) -> float:
    """Pearson correlation between the image and itself shifted by a fractional `lag` in device
    pixels (linear interpolation); 1.0 when the image is flat, which a seamless solid tiles to."""
    if not vertical:
        grid = [list(col) for col in zip(*grid, strict=True)]
    n, f = int(lag), lag - int(lag)
    height = len(grid)
    xs: list[float] = []
    ys: list[float] = []
    for y in range(height - n - 1):
        row_a, row_b, row_c = grid[y], grid[y + n], grid[y + n + 1]
        xs.extend(row_a)
        ys.extend((1 - f) * b + f * c for b, c in zip(row_b, row_c, strict=True))
    if not xs:
        return 1.0
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx < 1e-9 or syy < 1e-9:
        return 1.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    return sxy / (sxx * syy) ** 0.5


def trim(grid: list[list[float]], margin: int) -> list[list[float]]:
    return [row[margin:-margin] for row in grid[margin:-margin]]


def crop_to_ink(grid: list[list[float]], margin: int = 1) -> list[list[float]]:
    """Drop the unpainted rows and columns around the ink, then `margin` more on every side, so
    the element screenshot's clip rounding and the anti-aliased outer edge stay out of the sample."""

    def blank(line) -> bool:
        return all(v < 0.02 for v in line)

    rows = [list(row) for row in grid]
    while rows and blank(rows[0]):
        rows.pop(0)
    while rows and blank(rows[-1]):
        rows.pop()
    cols = [list(col) for col in zip(*rows, strict=True)]
    while cols and blank(cols[0]):
        cols.pop(0)
    while cols and blank(cols[-1]):
        cols.pop()
    return trim([list(row) for row in zip(*cols, strict=True)], margin)
