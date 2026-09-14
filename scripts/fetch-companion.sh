#!/usr/bin/env bash
# Fetch the four Monaspace Neon NF web faces the render matrix pairs the overlay
# against, into $1, which the caller then passes as MONASPACE_DIR. A TEST input
# only: nothing here is redistributed, and the font this repo builds contains no
# Monaspace outline.
#
# Digests are pinned because a swapped test input would silently change what the
# matrix proves. Recompute after a version bump with:
#   curl -sSL "<base>/MonaspaceNeonNF-<Face>.woff2" | sha256sum
set -euo pipefail

dest="${1:?usage: fetch-companion.sh <dir>}"
# renovate: datasource=github-releases depName=githubnext/monaspace
version="${MONASPACE_VERSION:-v1.400}"
base="https://raw.githubusercontent.com/githubnext/monaspace/${version}/fonts/Web%20Fonts/NerdFonts%20Web%20Fonts/Monaspace%20Neon"

declare -A digest=(
  [Regular]=8063ea45b6997c658035a4d876f996ecfa306c88fd0541d35d533fb1f9400c84
  [Bold]=45f56dceff8e569d61b6e3168fe208432e7bf0bc3e56e41b4d754cc575a063bd
  [Italic]=3d77eb9a5ec9e32c5ac7ea49c4325e5d6c8e5fefda7317527de905130a88f3cf
  [BoldItalic]=5dffc9465be18eb63263671f1f3ba266ede49043cb6b3edcd65ea993c909b3aa
)

mkdir -p "$dest"
for face in Regular Bold Italic BoldItalic; do
  out="$dest/MonaspaceNeonNF-${face}.woff2"
  want="${digest[$face]}"
  if [ -s "$out" ] && printf '%s  %s\n' "$want" "$out" | sha256sum --check --status; then
    continue
  fi
  # curl owns the output file, which is what makes --retry-all-errors safe: it
  # resets a partial write before retrying, and cannot with a pipe.
  curl --silent --show-error --location --connect-timeout 10 --max-time 120 \
    --retry 3 --retry-delay 5 --retry-all-errors \
    --output "$out" "${base}/MonaspaceNeonNF-${face}.woff2"
  printf '%s  %s\n' "$want" "$out" | sha256sum --check --status \
    || {
      printf 'fetch-companion: %s failed its digest\n' "$face" >&2
      exit 1
    }
done
printf 'fetch-companion: 4 faces verified in %s\n' "$dest"
