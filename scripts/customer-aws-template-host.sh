#!/usr/bin/env bash
set -euo pipefail

operation="${1:-}"
root="infrastructure/terraform/connection-template-host"

require() {
  local name="$1"
  [[ -n "${!name:-}" ]] || { echo "${name} is required" >&2; exit 2; }
}

require EXPECTED_AWS_ACCOUNT_ID
require TF_STATE_BUCKET
require TF_LOCK_TABLE
require AWS_REGION
require DAVDEPLOY_TEMPLATE_BUCKET

aws_args=()
if [[ -n "${AWS_PROFILE:-}" ]]; then
  aws_args+=(--profile "$AWS_PROFILE")
fi
account="$(aws sts get-caller-identity "${aws_args[@]}" --query Account --output text)"
[[ "$account" == "$EXPECTED_AWS_ACCOUNT_ID" ]] || { echo "AWS account guard failed" >&2; exit 3; }

terraform -chdir="$root" init -input=false \
  -backend-config="bucket=${TF_STATE_BUCKET}" \
  -backend-config="key=davdeploy/connection-template-host.tfstate" \
  -backend-config="dynamodb_table=${TF_LOCK_TABLE}" \
  -backend-config="region=${AWS_REGION}"

vars=("-var=region=${AWS_REGION}" "-var=bucket_name=${DAVDEPLOY_TEMPLATE_BUCKET}")
case "$operation" in
  plan) terraform -chdir="$root" plan -input=false "${vars[@]}" ;;
  apply)
    [[ "${CONFIRM_TEMPLATE_HOST_APPLY:-}" == "APPLY_DAVDEPLOY_TEMPLATE_HOST" ]] || {
      echo "Set CONFIRM_TEMPLATE_HOST_APPLY=APPLY_DAVDEPLOY_TEMPLATE_HOST after reviewing the plan" >&2; exit 2;
    }
    terraform -chdir="$root" apply -input=false -auto-approve "${vars[@]}"
    ;;
  destroy)
    [[ "${CONFIRM_TEMPLATE_HOST_DESTROY:-}" == "DESTROY_DAVDEPLOY_TEMPLATE_HOST" ]] || {
      echo "Set CONFIRM_TEMPLATE_HOST_DESTROY=DESTROY_DAVDEPLOY_TEMPLATE_HOST" >&2; exit 2;
    }
    terraform -chdir="$root" destroy -input=false -auto-approve "${vars[@]}"
    ;;
  *) echo "usage: $0 {plan|apply|destroy}" >&2; exit 2 ;;
esac
