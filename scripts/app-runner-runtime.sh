#!/usr/bin/env bash
set -euo pipefail

operation="${1:-}"
root="infrastructure/terraform/app-runner-runtime"

require() {
  local name="$1"
  [[ -n "${!name:-}" ]] || { echo "${name} is required" >&2; exit 2; }
}

require EXPECTED_AWS_ACCOUNT_ID
require TF_STATE_BUCKET
require TF_LOCK_TABLE
require AWS_REGION
require AGENTCONSTRUCT_AWS_CONNECTION_TEMPLATE_URL

aws_args=()
if [[ -n "${AWS_PROFILE:-}" ]]; then
  aws_args+=(--profile "$AWS_PROFILE")
fi
account="$(aws sts get-caller-identity "${aws_args[@]}" --query Account --output text)"
[[ "$account" == "$EXPECTED_AWS_ACCOUNT_ID" ]] || { echo "AWS account guard failed: got ${account}, expected ${EXPECTED_AWS_ACCOUNT_ID}" >&2; exit 3; }
[[ "${AGENTCONSTRUCT_PLATFORM_SCOPE:-platform}" == "platform" ]] || { echo "Platform deployment scope guard failed" >&2; exit 3; }

terraform -chdir="$root" init -input=false -reconfigure \
  -backend-config="bucket=${TF_STATE_BUCKET}" \
  -backend-config="key=agentconstruct/platform/app-runner-runtime.tfstate" \
  -backend-config="dynamodb_table=${TF_LOCK_TABLE}" \
  -backend-config="region=${AWS_REGION}"

image_identifier="${AGENTCONSTRUCT_RUNTIME_IMAGE_IDENTIFIER:-placeholder.invalid/agentconstruct:unset}"
enable_service="${AGENTCONSTRUCT_ENABLE_RUNTIME_SERVICE:-false}"
vars=(
  "-var=region=${AWS_REGION}"
  "-var=customer_template_url=${AGENTCONSTRUCT_AWS_CONNECTION_TEMPLATE_URL}"
  "-var=image_identifier=${image_identifier}"
  "-var=enable_service=${enable_service}"
  "-var=runtime_vpc_cidr=${AGENTCONSTRUCT_PLATFORM_VPC_CIDR:-10.42.0.0/16}"
)

case "$operation" in
  plan) terraform -chdir="$root" plan -input=false "${vars[@]}" ;;
  apply-foundation)
    [[ "${CONFIRM_RUNTIME_FOUNDATION_APPLY:-}" == "APPLY_AGENTCONSTRUCT_RUNTIME_FOUNDATION" ]] || {
      echo "Set CONFIRM_RUNTIME_FOUNDATION_APPLY=APPLY_AGENTCONSTRUCT_RUNTIME_FOUNDATION after reviewing the plan" >&2; exit 2;
    }
    terraform -chdir="$root" apply -input=false -auto-approve "${vars[@]}" ;;
  apply-service)
    [[ "${enable_service}" == "true" ]] || { echo "Set AGENTCONSTRUCT_ENABLE_RUNTIME_SERVICE=true" >&2; exit 2; }
    [[ "${image_identifier}" != "placeholder.invalid/agentconstruct:unset" ]] || { echo "Set AGENTCONSTRUCT_RUNTIME_IMAGE_IDENTIFIER" >&2; exit 2; }
    [[ "${CONFIRM_RUNTIME_SERVICE_APPLY:-}" == "APPLY_AGENTCONSTRUCT_RUNTIME_SERVICE" ]] || {
      echo "Set CONFIRM_RUNTIME_SERVICE_APPLY=APPLY_AGENTCONSTRUCT_RUNTIME_SERVICE after reviewing the plan" >&2; exit 2;
    }
    terraform -chdir="$root" apply -input=false -auto-approve "${vars[@]}" ;;
  destroy)
    [[ "${CONFIRM_RUNTIME_DESTROY:-}" == "DESTROY_AGENTCONSTRUCT_RUNTIME" ]] || {
      echo "Set CONFIRM_RUNTIME_DESTROY=DESTROY_AGENTCONSTRUCT_RUNTIME" >&2; exit 2;
    }
    terraform -chdir="$root" destroy -input=false -auto-approve "${vars[@]}" ;;
  output) terraform -chdir="$root" output -json ;;
  *) echo "usage: $0 {plan|apply-foundation|apply-service|destroy|output}" >&2; exit 2 ;;
esac
