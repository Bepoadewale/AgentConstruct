#!/usr/bin/env bash
set -euo pipefail

styles="$(curl -fsS http://127.0.0.1:8080/styles.css)"

for marker in \
  '@media (max-width:720px)' \
  '@media (max-width:620px)' \
  '@media (prefers-reduced-motion:reduce)' \
  '@media (prefers-color-scheme:dark)' \
  '.activity-drawer-card' \
  '.compare-toolbar' \
  '.sr-only' \
  '.skeleton-list'; do
  grep -q "$marker" <<<"$styles"
done

echo "Frontend responsive contract passed."
