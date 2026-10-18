#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${1:-${repo_root}/dist/lambda}"
build_root="$(mktemp -d "${TMPDIR:-/tmp}/agentconstruct-lambda.XXXXXX")"

cleanup() {
  case "${build_root}" in
    "${TMPDIR:-/tmp}"/agentconstruct-lambda.*) rm -rf -- "${build_root}" ;;
    *) printf 'Refusing to clean unexpected path: %s\n' "${build_root}" >&2 ;;
  esac
}
trap cleanup EXIT

mkdir -p "${output_dir}" "${build_root}/package"
python3.12 -m pip install --quiet --disable-pip-version-check --target "${build_root}/package" "${repo_root}"
find "${build_root}/package" -type d -name '__pycache__' -prune -exec rm -rf -- {} +
(
  cd "${build_root}/package"
  zip -qr "${output_dir}/agentconstruct-control-plane.zip" .
)
printf 'Built %s\n' "${output_dir}/agentconstruct-control-plane.zip"
