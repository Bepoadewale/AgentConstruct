#!/usr/bin/env bash
set -euo pipefail

page="$(curl -fsS http://127.0.0.1:8080/)"
javascript="$(curl -fsS http://127.0.0.1:8080/app.js)"
for marker in \
  'aria-label=' \
  'aria-live=' \
  'aria-expanded=' \
  'role="dialog"' \
  'id="close-activity-drawer"' \
  'id="command-search"'; do
  grep -q "$marker" <<<"$page"
done
grep -q 'event.key === "Tab"' <<<"$javascript"
echo "Frontend accessibility contract passed."
