#!/usr/bin/env bash
set -euo pipefail

# Deterministic browser-facing contract check. Compose E2E drives the API flow.
page="$(curl -fsS http://127.0.0.1:8080/)"
grep -q 'Describe the AI system you want to deploy' <<<"$page"
grep -q 'region' <<<"$page"
grep -q 'data-classification' <<<"$page"
grep -q 'id="budget"' <<<"$page"
grep -q 'Cheapest simple option that meets the request' <<<"$page"
javascript="$(curl -fsS http://127.0.0.1:8080/app.js)"
grep -q 'waitForWorker' <<<"$javascript"
grep -q 'renderAlternatives' <<<"$javascript"
echo "Browser-facing UI contract passed."
