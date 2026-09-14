"""Closed-contour primitives in integer font units.

A contour is a list whose first element is an (x, y) point and whose later elements are either an
(x, y) line target or an (x1, y1, x2, y2, x, y) cubic Bezier; it closes back to the first point.
Filled contours run counter-clockwise (y up), holes clockwise.
"""

import math

Point = tuple[int, int]
Segment = tuple[int, ...]
Contour = list[Segment]


def r(v: float) -> int:
    return math.floor(v + 0.5)


def rect(x0: int, x1: int, y0: int, y1: int) -> Contour:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def signed_area(points: list[tuple[float, float]]) -> float:
    total = 0.0
    for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1], strict=True):
        total += ax * by - bx * ay
    return total / 2


def polygon(points: list[tuple[float, float]], *, hole: bool = False) -> Contour:
    """A simple polygon, re-oriented to the filling convention and deduplicated after rounding;
    empty when fewer than three distinct points remain."""
    pts = [(r(x), r(y)) for x, y in points]
    if len(pts) < 3:
        return []
    if (signed_area(pts) < 0) != hole:
        pts.reverse()
    out: list[Point] = []
    for p in pts:
        if not out or p != out[-1]:
            out.append(p)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    return out if len(out) >= 3 else []


def clip(
    points: list[tuple[float, float]], a: float, b: float, c: float
) -> list[tuple[float, float]]:
    """Sutherland-Hodgman: keep the part of the polygon where a*x + b*y + c >= 0."""
    out: list[tuple[float, float]] = []
    for (px, py), (qx, qy) in zip(points, points[1:] + points[:1], strict=True):
        dp = a * px + b * py + c
        dq = a * qx + b * qy + c
        if dp >= 0:
            out.append((px, py))
        if (dp >= 0) != (dq >= 0):
            t = dp / (dp - dq)
            out.append((px + t * (qx - px), py + t * (qy - py)))
    return out


def half_plane(
    p: tuple[float, float], q: tuple[float, float], side: int
) -> tuple[float, float, float]:
    """Coefficients of the half-plane bounded by line p->q; side +1 keeps its left, -1 its right."""
    a = -(q[1] - p[1]) * side
    b = (q[0] - p[0]) * side
    return a, b, -(a * p[0] + b * p[1])


def arc(cx: float, cy: float, rx: float, ry: float, a0: float, a1: float) -> list[Segment]:
    """Cubic segments along an ellipse from angle a0 to a1 (degrees, counter-clockwise when
    a1 > a0), excluding the start point; one segment per quarter turn or less."""
    steps = max(1, math.ceil(abs(a1 - a0) / 90 - 1e-9))
    out: list[Segment] = []
    for i in range(steps):
        t0 = math.radians(a0 + (a1 - a0) * i / steps)
        t1 = math.radians(a0 + (a1 - a0) * (i + 1) / steps)
        k = 4 / 3 * math.tan((t1 - t0) / 4)
        c0x, c0y = math.cos(t0), math.sin(t0)
        c1x, c1y = math.cos(t1), math.sin(t1)
        out.append(
            (
                r(cx + rx * (c0x - k * c0y)),
                r(cy + ry * (c0y + k * c0x)),
                r(cx + rx * (c1x + k * c1y)),
                r(cy + ry * (c1y - k * c1x)),
                r(cx + rx * c1x),
                r(cy + ry * c1y),
            )
        )
    return out


def arc_start(cx: float, cy: float, rx: float, ry: float, a0: float) -> Point:
    return r(cx + rx * math.cos(math.radians(a0))), r(cy + ry * math.sin(math.radians(a0)))


def ellipse(cx: float, cy: float, rx: float, ry: float, *, hole: bool = False) -> Contour:
    a0, a1 = (0, -360) if hole else (0, 360)
    return [arc_start(cx, cy, rx, ry, a0), *arc(cx, cy, rx, ry, a0, a1)]


def ring(cx: float, cy: float, outer: float, inner: float) -> list[Contour]:
    return [ellipse(cx, cy, outer, outer), ellipse(cx, cy, inner, inner, hole=True)]


def arc_band(cx: float, cy: float, outer: float, inner: float, a0: float, a1: float) -> Contour:
    """The region between two concentric arcs from a0 to a1 with flat ends."""
    a0, a1 = min(a0, a1), max(a0, a1)
    return [
        arc_start(cx, cy, outer, outer, a0),
        *arc(cx, cy, outer, outer, a0, a1),
        arc_start(cx, cy, inner, inner, a1),
        *arc(cx, cy, inner, inner, a1, a0),
    ]
