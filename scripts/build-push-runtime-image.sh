#!/usr/bin/env bash
set -euo pipefail

require() {
  local name="$1"
  [[ -n "${!name:-}" ]] || { echo "${name} is required" >&2; exit 2; }
}

require AWS_REGION
require AGENTCONSTRUCT_RUNTIME_ECR_REPOSITORY_URL

tag="${AGENTCONSTRUCT_RUNTIME_IMAGE_TAG:-$(git rev-parse --short=12 HEAD)}"
repo="${AGENTCONSTRUCT_RUNTIME_ECR_REPOSITORY_URL}"
registry="${repo%%/*}"
aws_args=()
if [[ -n "${AWS_PROFILE:-}" ]]; then
  aws_args+=(--profile "$AWS_PROFILE")
fi
aws ecr get-login-password "${aws_args[@]}" --region "$AWS_REGION" | docker login --username AWS --password-stdin "$registry"
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  --push \
  -t "${repo}:${tag}" \
  -f apps/api/Dockerfile \
  .
printf '%s:%s\n' "$repo" "$tag"
