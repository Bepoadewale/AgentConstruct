#!/usr/bin/env bash
set -euo pipefail

base_url="${AGENTCONSTRUCT_API_BASE_URL:-http://127.0.0.1:8080}"
allowed_origin="${AGENTCONSTRUCT_TEST_FRONTEND_ORIGIN:-http://localhost:5173}"
headers_file="$(mktemp -t agentconstruct-api-headers.XXXXXX)"
trap 'rm -f "$headers_file"' EXIT

root="$(curl -fsS "$base_url/")"
grep -q '"surface":"control-plane-api"' <<<"$root"
grep -q '"api_version":"v1"' <<<"$root"

openapi="$(curl -fsS "$base_url/openapi.json")"
grep -q '"/api/v1/customer-plans/revisions/{revision_id}/submit"' <<<"$openapi"
grep -q '"/api/v1/customer-plans/revisions/{revision_id}/approve"' <<<"$openapi"

curl -fsS -o /dev/null -D "$headers_file" -X OPTIONS "$base_url/api/v1/me" \
  -H "Origin: $allowed_origin" \
  -H 'Access-Control-Request-Method: GET' \
  -H 'Access-Control-Request-Headers: authorization'
grep -qi "^access-control-allow-origin: $allowed_origin" "$headers_file"
if grep -qi '^access-control-allow-credentials: true' "$headers_file"; then
  echo "CORS must not enable credential cookies." >&2
  exit 1
fi

curl -sS -o /dev/null -D "$headers_file" -X OPTIONS "$base_url/api/v1/me" \
  -H 'Origin: https://attacker.example.com' \
  -H 'Access-Control-Request-Method: GET'
if grep -qi '^access-control-allow-origin:' "$headers_file"; then
  echo "Unconfigured origin received a CORS allow header." >&2
  exit 1
fi

echo "Versioned API and exact-origin CORS contract passed."

