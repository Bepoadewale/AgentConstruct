#!/usr/bin/env bash
set -euo pipefail

operation="${1:-}"
root="infrastructure/terraform/customer-connection"

require() {
  local name="$1"
  [[ -n "${!name:-}" ]] || { echo "${name} is required" >&2; exit 2; }
}

check_identity() {
  require EXPECTED_AWS_ACCOUNT_ID
  local account
  if [[ -n "${AWS_PROFILE:-}" ]]; then
    account="$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)"
  else
    account="$(aws sts get-caller-identity --query Account --output text)"
  fi
  [[ "$account" == "$EXPECTED_AWS_ACCOUNT_ID" ]] || { echo "AWS account guard failed" >&2; exit 3; }
}

connection_init() {
  require TF_STATE_BUCKET
  require TF_LOCK_TABLE
  require AWS_REGION
  require CUSTOMER_CONNECTION_ID
  terraform -chdir="$root" init -input=false \
    -backend-config="bucket=${TF_STATE_BUCKET}" \
    -backend-config="key=agentconstruct/customer-connections/${CUSTOMER_CONNECTION_ID}.tfstate" \
    -backend-config="dynamodb_table=${TF_LOCK_TABLE}" \
    -backend-config="region=${AWS_REGION}"
}

connection_vars=(
  "-var=region=${AWS_REGION:-}"
  "-var=customer_connection_id=${CUSTOMER_CONNECTION_ID:-}"
  "-var=agentconstruct_control_plane_role_arn=${AGENTCONSTRUCT_CONTROL_PLANE_ROLE_ARN:-}"
  "-var=external_id=${AGENTCONSTRUCT_EXTERNAL_ID:-}"
)

case "$operation" in
  plan)
    check_identity; require AGENTCONSTRUCT_CONTROL_PLANE_ROLE_ARN; require AGENTCONSTRUCT_EXTERNAL_ID
    connection_init
    terraform -chdir="$root" plan -input=false "${connection_vars[@]}"
    ;;
  apply)
    check_identity; require AGENTCONSTRUCT_CONTROL_PLANE_ROLE_ARN; require AGENTCONSTRUCT_EXTERNAL_ID
    [[ "${CONFIRM_CUSTOMER_CONNECTION_APPLY:-}" == "APPLY_AGENTCONSTRUCT_CUSTOMER_CONNECTION" ]] || {
      echo "Set CONFIRM_CUSTOMER_CONNECTION_APPLY=APPLY_AGENTCONSTRUCT_CUSTOMER_CONNECTION after reviewing the plan" >&2
      exit 2
    }
    connection_init
    terraform -chdir="$root" apply -input=false "${connection_vars[@]}"
    ;;
  destroy)
    check_identity; require AGENTCONSTRUCT_CONTROL_PLANE_ROLE_ARN; require AGENTCONSTRUCT_EXTERNAL_ID
    [[ "${CONFIRM_CUSTOMER_CONNECTION_DESTROY:-}" == "DESTROY_AGENTCONSTRUCT_CUSTOMER_CONNECTION" ]] || {
      echo "Set CONFIRM_CUSTOMER_CONNECTION_DESTROY=DESTROY_AGENTCONSTRUCT_CUSTOMER_CONNECTION" >&2
      exit 2
    }
    connection_init
    terraform -chdir="$root" destroy -input=false "${connection_vars[@]}"
    ;;
  *)
    echo "usage: $0 {plan|apply|destroy}" >&2
    exit 2
    ;;
esac
