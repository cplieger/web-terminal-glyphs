#!/usr/bin/env bash
# Cut a semver release from conventional-commit subjects since the last tag and
# attach dist/* at creation. Runs after build and both test tiers in
# publish.yaml; DRY_RUN=1 prints the decision and creates nothing.
set -euo pipefail

REPO="${GITHUB_REPOSITORY:-cplieger/web-terminal-glyphs}"
DIST="${DIST:-dist}"

last="$(git describe --tags --abbrev=0 --match 'v*' 2>/dev/null || true)"
range="${last:+${last}..HEAD}"
range="${range:-HEAD}"

subjects="$(git log --format='%s' "$range" -- . ':!*.md' ':!.editorconfig' ':!.gitattributes' ':!.gitignore' ':!renovate.json')"
bodies="$(git log --format='%b' "$range")"

bump=""
if grep -qE '^[a-z]+(\([^)]*\))?!:' <<<"$subjects" || grep -q '^BREAKING CHANGE:' <<<"$bodies"; then
  bump="major"
elif grep -qE '^feat(\([^)]*\))?:' <<<"$subjects"; then
  bump="minor"
elif grep -qE '^(fix|perf|sec|refactor|chore\(deps\))(\([^)]*\))?:' <<<"$subjects"; then
  bump="patch"
fi

if [ -z "$bump" ]; then
  echo "release: no releasing commit since ${last:-the beginning}; nothing to cut"
  exit 0
fi

if [ -z "$last" ]; then
  next="v1.0.0"
else
  IFS=. read -r major minor patch <<<"${last#v}"
  case "$bump" in
    major) next="v$((major + 1)).0.0" ;;
    minor) next="v${major}.$((minor + 1)).0" ;;
    patch) next="v${major}.${minor}.$((patch + 1))" ;;
  esac
fi

for f in WebTerminalGlyphs.woff2 cell.json LICENSE NOTICE; do
  [ -s "$DIST/$f" ] || {
    echo "release: $DIST/$f missing or empty" >&2
    exit 1
  }
done

notes="$(printf '## %s\n\n%s\n' "$next" "$(sed 's/^/- /' <<<"$subjects")")"
echo "release: ${last:-<none>} -> $next ($bump)"

if [ "${DRY_RUN:-0}" = "1" ]; then
  printf '%s\n' "$notes"
  exit 0
fi

if gh release view "$next" --repo "$REPO" >/dev/null 2>&1; then
  echo "release: $next already exists; nothing to do"
  exit 0
fi

sha="$(git rev-parse HEAD)"
gh api --method POST "repos/${REPO}/git/refs" --raw-field ref="refs/tags/${next}" --raw-field sha="$sha" >/dev/null
gh release create "$next" "$DIST"/WebTerminalGlyphs.woff2 "$DIST"/cell.json "$DIST"/LICENSE "$DIST"/NOTICE \
  --repo "$REPO" --title "$next" --notes "$notes" --latest
echo "release: created $next with 4 assets"
