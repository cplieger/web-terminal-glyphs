"""The render matrix: the fixtures page served from tests/fixtures over a local HTTP server, one
browser context per device scale factor, page zoom set on <html>.

Environment: MONASPACE_DIR (required) is the directory holding the companion's four WOFF2 files,
copied into tests/fixtures/base for the session and removed after it; GLYPHS_DIST points at
another build (the mutation checks); GLYPHS_STACK=base renders the .term rows with the companion
alone (the red check for the face-identity and seam oracles).
"""

import os
import shutil
import statistics
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.render import pixels

if TYPE_CHECKING:
    from playwright.sync_api import Browser, Page

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / 'tests' / 'fixtures'
DIST = Path(os.environ.get('GLYPHS_DIST', ROOT / 'dist'))
COMPANION_FILES = tuple(
    f'MonaspaceNeonNF-{face}.woff2' for face in ('Regular', 'Bold', 'Italic', 'BoldItalic')
)
FONT_FILE = 'WebTerminalGlyphs.woff2'
DPRS = (1, 2)
ZOOMS = (1.0, 1.1)
SOLID_CELL = '\u2588'
PROFILE_SPAN = 7
# The share of the measured solid level a boundary pixel may lose before it counts as a seam.
# Both poles measured: a correct build loses at most 2.0% (250/255 on the boundary column,
# chromium 151 on the ubuntu-24.04 runner at DPR 1, zoom 1.1) while OVERHANG_UNITS = 0 loses 14.1%
# at its shallowest across the three engines (Firefox, stacked half blocks, DPR 1, zoom 1.1) and
# 88.6% at its deepest.
MAX_BOUNDARY_LOSS = 0.05


def pytest_configure(config) -> None:
    """The matrix is the three engines; a bare `pytest tests/render` runs them all."""
    if not config.option.browser:
        config.option.browser = ['chromium', 'firefox', 'webkit']


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def profile(line: list[float], index: int) -> str:
    """The ink either side of `index`, bracketed, with the rest of the line summarised: a seam is
    one pixel deep, so its neighbours are the diagnosis and the far end is context."""
    lo, hi = max(0, index - PROFILE_SPAN), min(len(line), index + PROFILE_SPAN + 1)
    around = ' '.join(
        f'[{v:.3f}]' if i + lo == index else f'{v:.3f}' for i, v in enumerate(line[lo:hi])
    )
    return f'{lo}..{hi - 1} {around} (line min {min(line):.3f}, len {len(line)})'


def companion_dir() -> Path:
    where = os.environ.get('MONASPACE_DIR')
    missing = [f for f in COMPANION_FILES if not where or not (Path(where) / f).is_file()]
    if missing:
        pytest.fail(
            f'MONASPACE_DIR={where!r} must name a directory holding the companion faces '
            f'{", ".join(COMPANION_FILES)} (the Neon NF variant of a githubnext/monaspace '
            f'release; not vendored here); missing: {", ".join(missing)}',
            pytrace=False,
        )
    return Path(where)


@pytest.fixture(scope='session')
def fixtures_dir() -> Path:
    companion = companion_dir()
    base, dist = FIXTURES / 'base', FIXTURES / 'dist'
    for folder in (base, dist):
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir()
    for name in COMPANION_FILES:
        shutil.copy(companion / name, base / name)
    if not (DIST / FONT_FILE).exists():
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'build.py'), str(DIST)], check=True)
    shutil.copy(DIST / FONT_FILE, dist / FONT_FILE)
    yield FIXTURES
    for folder in (base, dist):
        shutil.rmtree(folder, ignore_errors=True)


@pytest.fixture(scope='session')
def page_url(fixtures_dir: Path) -> str:
    server = ThreadingHTTPServer(
        ('127.0.0.1', 0), partial(QuietHandler, directory=str(fixtures_dir))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{server.server_address[1]}/page.html'
    server.shutdown()


@pytest.fixture(params=DPRS, ids=[f'dpr{d}' for d in DPRS])
def dpr(request) -> int:
    return request.param


@pytest.fixture(params=ZOOMS, ids=[f'zoom{z}' for z in ZOOMS])
def zoom(request) -> float:
    return request.param


@pytest.fixture(scope='session')
def contexts(browser: Browser):
    cache = {}
    yield cache
    for context in cache.values():
        context.close()


class Term:
    """One fixture page: rows go in through set_rows, measurements come out as ink grids."""

    def __init__(self, page: Page, browser_name: str, dpr: int, zoom: float):
        self.page, self.browser_name, self.dpr, self.zoom = page, browser_name, dpr, zoom
        self.scale = dpr * zoom
        self.solid: float | None = None

    def set_rows(self, cls: str, rows: list[list[str]]) -> None:
        self.page.evaluate('([cls, rows]) => window.setRows(cls, rows)', [cls, rows])

    def probe(self, row: int) -> dict:
        return self.page.evaluate('i => window.probe(i)', row)

    def ink(self, selector: str) -> list[list[float]]:
        return pixels.ink(pixels.decode(self.page.locator(selector).screenshot(type='png')))

    def png(self, selector: str) -> bytes:
        return self.page.locator(selector).screenshot(type='png')

    def solid_level(self) -> float:
        """The ink level this host, engine and scale paint a fully covered device pixel at,
        sampled from inside one cell so neither a cell boundary nor the overhang enters it. It
        replaces the page's rows, so read it through the `ink_floor` fixture rather than mid-test.
        """
        if self.solid is None:
            self.set_rows('ov', [[SOLID_CELL]])
            grid = pixels.crop_to_ink(self.ink('#block .row span'), 2)
            self.solid = statistics.median(v for row in grid for v in row)
        return self.solid

    def diagnose(self, grid: list[list[float]], y: int, x: int, floor: float, sel: str) -> str:
        """What a seam failure has to carry to be actionable from CI alone; `sel` names a node
        carrying text, whose painting font is the other half of the diagnosis. Reads no page state
        beyond that, so the caller's rows are still the ones measured."""
        box = pixels.ink_box(grid)
        lines = [
            (
                f'ink {grid[y][x]:.3f} at column {x}, row {y}, below floor {floor:.3f} '
                f'(solid {self.solid_level():.3f} less {MAX_BOUNDARY_LOSS:.0%})'
            ),
            (
                f'{self.browser_name} dpr{self.dpr} zoom{self.zoom}, ink box {box} '
                f'in a {len(grid[0])}x{len(grid)} grid'
            ),
            f'row {y}: {profile(grid[y], x)}',
            f'column {x}: {profile([row[x] for row in grid], y)}',
        ]
        if self.browser_name == 'chromium':
            lines.append(f'painted by {", ".join(self.fonts(sel)) or "nothing"}')
        return '\n'.join(lines)

    def fonts(self, selector: str) -> list[str]:
        """Chromium only: the platform font family names that painted the node."""
        cdp = self.page.context.new_cdp_session(self.page)
        cdp.send('DOM.enable')
        cdp.send('CSS.enable')
        root = cdp.send('DOM.getDocument', {'depth': -1})['root']
        node = cdp.send('DOM.querySelector', {'nodeId': root['nodeId'], 'selector': selector})
        fonts = cdp.send('CSS.getPlatformFontsForNode', {'nodeId': node['nodeId']})['fonts']
        cdp.detach()
        return [f['familyName'] for f in fonts if f['glyphCount'] > 0]


@pytest.fixture
def term(
    browser: Browser, browser_name: str, contexts: dict, page_url: str, dpr: int, zoom: float
) -> Term:
    if dpr not in contexts:
        contexts[dpr] = browser.new_context(
            viewport={'width': 800, 'height': 600}, device_scale_factor=dpr
        )
    page = contexts[dpr].new_page()
    page.goto(page_url, wait_until='load')
    page.evaluate('z => { document.documentElement.style.zoom = z; }', zoom)
    if os.environ.get('GLYPHS_STACK') == 'base':
        page.add_style_tag(content='.term { font-family: "Monaspace Neon NF", monospace; }')
    yield Term(page, browser_name, dpr, zoom)
    page.close()


@pytest.fixture
def ink_floor(term: Term) -> float:
    """The level a boundary pixel must reach to count as covered, measured in the same page and
    run as the subject: an absolute threshold held here and failed on the ubuntu-24.04 runner,
    where a correct build reads 250/255 on the boundary column that reads 255/255 locally.

    A fixture, not a call in the test body, because measuring it replaces the page's rows.
    """
    return term.solid_level() * (1 - MAX_BOUNDARY_LOSS)
