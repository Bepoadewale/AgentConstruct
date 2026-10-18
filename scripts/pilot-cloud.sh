#!/usr/bin/env bash
set -euo pipefail

operation="${1:-}"
project="${PROJECT:-davdeploy}"
environment="${ENVIRONMENT:-pilot}"

require() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "${name} is required" >&2
    exit 2
  fi
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

pilot_init() {
  require TF_STATE_BUCKET
  require TF_LOCK_TABLE
  require AWS_REGION
  terraform -chdir=infrastructure/terraform/pilot init -input=false \
    -backend-config="bucket=${TF_STATE_BUCKET}" \
    -backend-config="key=${project}/${environment}.tfstate" \
    -backend-config="dynamodb_table=${TF_LOCK_TABLE}" \
    -backend-config="region=${AWS_REGION}"
}

pilot_vars=("-var=region=${AWS_REGION:-}" "-var=project=${project}" "-var=environment=${environment}" "-var=vpc_cidr=${VPC_CIDR:-10.72.0.0/20}" "-var=availability_zones=[\"${AWS_REGION:-us-east-1}a\",\"${AWS_REGION:-us-east-1}b\"]")

case "$operation" in
  guardrails-plan)
    check_identity; require TF_VAR_state_bucket_name; require TF_VAR_monthly_budget_usd; require TF_VAR_budget_notification_email; require AWS_REGION
    terraform -chdir=infrastructure/terraform/bootstrap init -backend=false -input=false
    terraform -chdir=infrastructure/terraform/bootstrap plan -input=false -var="region=${AWS_REGION}" -var="project=${project}" ;;
  plan)
    check_identity; pilot_init; terraform -chdir=infrastructure/terraform/pilot plan -input=false "${pilot_vars[@]}" ;;
  apply)
    check_identity; [[ "${CONFIRM_APPLY:-}" == "APPLY_DAVDEPLOY_PILOT" ]] || { echo "Set CONFIRM_APPLY=APPLY_DAVDEPLOY_PILOT" >&2; exit 2; }
    pilot_init; terraform -chdir=infrastructure/terraform/pilot apply -input=false "${pilot_vars[@]}" ;;
  destroy)
    check_identity; [[ "${CONFIRM_DESTROY:-}" == "DESTROY_DAVDEPLOY_PILOT" ]] || { echo "Set CONFIRM_DESTROY=DESTROY_DAVDEPLOY_PILOT" >&2; exit 2; }
    pilot_init; terraform -chdir=infrastructure/terraform/pilot destroy -input=false "${pilot_vars[@]}" ;;
  push-image|bootstrap-runtime|smoke|validate)
    echo "${operation} is a future runtime action. See docs/cloud-operations.md; it needs a reviewed EKS cluster and scoped role." ;;
  *)
    echo "usage: $0 {guardrails-plan|plan|apply|destroy|push-image|bootstrap-runtime|smoke|validate}" >&2; exit 2 ;;
esac
