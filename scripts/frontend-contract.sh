#!/usr/bin/env bash
set -euo pipefail

page="$(curl -fsS http://127.0.0.1:8080/)"
javascript="$(curl -fsS http://127.0.0.1:8080/app.js)"
for marker in 'revision-comparison' 'compare-revisions' 'audit-group' 'activity-drawer' 'export-review' 'copy-review-link' 'load-sample-plan' 'history-refresh' 'id="help"'; do
  grep -q "$marker" <<<"$page"
done
for marker in 'compareRevisions' 'eventFamily' 'exportReviewSummary' 'track(' 'setRegionLoading' 'withRetry' 'stableCache' 'history-refresh' 'skeleton-list' 'load-sample-plan'; do
  grep -q "$marker" <<<"$javascript"
done
node --check <(printf '%s' "$javascript")
echo "Frontend interaction contract passed."
