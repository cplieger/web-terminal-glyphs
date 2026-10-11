#!/usr/bin/env bash
# Cut a semver release when the built assets differ from the latest release's,
# attaching dist/* at creation. Runs after build and both test tiers in
# publish.yaml; DRY_RUN=1 prints the decision and creates nothing.
set -euo pipefail

REPO="${GITHUB_REPOSITORY:-cplieger/web-terminal-glyphs}"
DIST="${DIST:-dist}"
ASSETS=(WebTerminalGlyphs.woff2 cell.json LICENSE NOTICE)

for f in "${ASSETS[@]}"; do
  [ -s "$DIST/$f" ] || {
    echo "release: $DIST/$f missing or empty" >&2
    exit 1
  }
done

last="$(git describe --tags --abbrev=0 --match 'v*' 2>/dev/null || true)"
changed=""

# The release is the four assets, so identical bytes publish nothing whatever
# the commits say: a dev-only lock bump or a CI pin would otherwise cut a
# version consumers gain nothing from. The build is deterministic, which is
# what makes a byte compare meaningful.
if [ -n "$last" ]; then
  prev="$(mktemp -d)"
  trap 'rm -rf "$prev"' EXIT
  gh release download "$last" --repo "$REPO" --dir "$prev" "${ASSETS[@]/#/--pattern=}"
  for f in "${ASSETS[@]}"; do
    cmp -s "$DIST/$f" "$prev/$f" || changed+=" $f"
  done
  if [ -z "$changed" ]; then
    echo "release: assets match ${last}; nothing to cut"
    exit 0
  fi
  echo "release: changed since ${last}:${changed}"
fi

range="${last:+${last}..HEAD}"
range="${range:-HEAD}"
subjects="$(git log --format='%s' "$range" -- . ':!*.md' ':!.editorconfig' ':!.gitattributes' ':!.gitignore' ':!renovate.json')"
bodies="$(git log --format='%b' "$range")"

# Changed bytes always ship, so patch is the floor and commits only raise it.
bump="patch"
if grep -qE '^[a-z]+(\([^)]*\))?!:' <<<"$subjects" || grep -q '^BREAKING CHANGE:' <<<"$bodies"; then
  bump="major"
elif grep -qE '^feat(\([^)]*\))?:' <<<"$subjects"; then
  bump="minor"
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

notes="$(printf '## %s\n\n%s\n' "$next" "$(sed 's/^/- /' <<<"${subjects:-rebuilt assets:${changed}}")")"
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
branch="${GITHUB_REF_NAME:-main}"
head="$(gh api "repos/${REPO}/git/ref/heads/${branch}" --jq '.object.sha')"
if [ "$sha" != "$head" ]; then
  # A push landed while this run was building, so the run for that commit cuts
  # this version from a tree containing ours. Tagging here would fail anyway:
  # the Actions token may not create a tag at a commit the branch has moved
  # past once the newer commits touch .github/workflows, and `permissions:`
  # cannot grant the `workflows` scope that would allow it.
  echo "release: ${branch} moved to ${head}; the run for that commit cuts ${next}"
  exit 0
fi

gh api --method POST "repos/${REPO}/git/refs" --raw-field ref="refs/tags/${next}" --raw-field sha="$sha" >/dev/null
gh release create "$next" "${ASSETS[@]/#/$DIST/}" \
  --repo "$REPO" --title "$next" --notes "$notes" --latest
echo "release: created $next with ${#ASSETS[@]} assets"
