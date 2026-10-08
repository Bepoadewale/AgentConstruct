#!/usr/bin/env bash
set -euo pipefail

wait_for() {
  local label="$1" url="$2"
  for _ in $(seq 1 60); do
    if curl -fsS "$url" >/dev/null 2>&1; then echo "$label ready"; return 0; fi
    sleep 1
  done
  echo "$label did not become ready: $url" >&2
  exit 1
}

wait_for api http://127.0.0.1:8080/healthz
wait_for executor http://127.0.0.1:8090/healthz
wait_for prometheus http://127.0.0.1:9090/-/ready
wait_for grafana http://127.0.0.1:3000/api/health
curl -fsS http://127.0.0.1:8181/health >/dev/null
echo "OPA ready"
