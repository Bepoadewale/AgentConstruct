#!/usr/bin/env bash
set -euo pipefail

# Deterministic browser-facing contract check. Compose E2E drives the API flow.
page="$(curl -fsS http://127.0.0.1:8080/)"
grep -q 'Describe the AI system you want to deploy' <<<"$page"
grep -q 'region' <<<"$page"
grep -q 'data-classification' <<<"$page"
grep -q 'id="budget"' <<<"$page"
grep -q 'Cheapest simple option that meets the request' <<<"$page"
grep -q 'Connect AWS account' <<<"$page"
grep -q 'GitHub connection' <<<"$page"
grep -q 'repository-branch' <<<"$page"
grep -q 'Continue as developer' <<<"$page"
grep -q 'Continue as administrator' <<<"$page"
javascript="$(curl -fsS http://127.0.0.1:8080/app.js)"
grep -q 'waitForWorker' <<<"$javascript"
grep -q 'renderAlternatives' <<<"$javascript"
grep -q 'aws-quick-create' <<<"$javascript"
grep -q 'aws-verify' <<<"$javascript"
grep -q 'refreshDashboard' <<<"$javascript"
grep -q 'refreshGitHubConnection' <<<"$javascript"
grep -q 'disconnect-aws' <<<"$javascript"
echo "Browser-facing UI contract passed."
