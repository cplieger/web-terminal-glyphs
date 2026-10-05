# Contributing to web-terminal-glyphs

The [shared rules](https://github.com/cplieger/.github/blob/main/CONTRIBUTING.md) for commits, releases, synced files, checks and review apply here, except where the release facts below differ from them.

## Rules

- A Monaspace version bump re-measures the companion with fontTools and lands in one commit. That commit updates the version and digests in `scripts/fetch-companion.sh`, `SOURCE` in `glyphs/companion.py`, the measured constants in `glyphs/cell.py`, the shade dots in `glyphs/families/shade.py` and the companion literals in the geometry tests.
- The geometry tests compare the font with those literals and never open the companion file. A bump that skips the measurements passes them, and the font keeps the old face's strokes, shade dots and line metrics.
- A change to the glyph tables or to `LEFT_TO_COMPANION` in `glyphs/companion.py` updates the codepoint counts in `README.md` and `docs/how-it-works.md`. No check derives them from the code, so a green build leaves both pages stale.

## Checks

Pull request CI builds no font and runs neither test tier. Both tiers run only in the Publish workflow, after the merge, so run the README's [Building](README.md#building) commands before you push.

Rebuild with `uv run scripts/build.py` after each change to `glyphs/` or `scripts/build.py`. Both test tiers test the font already in `dist/` and build one only when it is missing, so a stale build passes.

## Releases

A releasing commit that touches only `tests/`, `LICENSE` or `.github/` still publishes a new font release here.

A type the shared table does not name, such as `build:`, does not release. A `!` after any type, or a `BREAKING CHANGE:` footer on any commit, is a major release.

The release notes here list commit subjects as written, whatever their type, and never print a `BREAKING CHANGE:` footer. A breaking change states what a consumer must change in its subject.
