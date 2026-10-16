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
enable_durable_database="${AGENTCONSTRUCT_ENABLE_DURABLE_DATABASE:-true}"
enable_nova_model="${AGENTCONSTRUCT_ENABLE_NOVA_MODEL:-true}"
database_deletion_protection="${AGENTCONSTRUCT_DATABASE_DELETION_PROTECTION:-true}"
monitoring_email="${AGENTCONSTRUCT_ALERT_EMAIL:-}"
oidc_jwks_url="${AGENTCONSTRUCT_JWKS_URL:-}"
oidc_issuer="${AGENTCONSTRUCT_OIDC_ISSUER:-}"
oidc_audience="${AGENTCONSTRUCT_OIDC_AUDIENCE:-}"
policy_url="${AGENTCONSTRUCT_OPA_URL:-}"
vars=(
  "-var=region=${AWS_REGION}"
  "-var=customer_template_url=${AGENTCONSTRUCT_AWS_CONNECTION_TEMPLATE_URL}"
  "-var=image_identifier=${image_identifier}"
  "-var=enable_service=${enable_service}"
  "-var=enable_durable_database=${enable_durable_database}"
  "-var=enable_nova_model=${enable_nova_model}"
  "-var=database_deletion_protection=${database_deletion_protection}"
  "-var=runtime_vpc_cidr=${AGENTCONSTRUCT_PLATFORM_VPC_CIDR:-10.42.0.0/16}"
  "-var=monthly_platform_budget_usd=${AGENTCONSTRUCT_PLATFORM_MONTHLY_BUDGET_USD:-250}"
  "-var=monitoring_notification_email=${monitoring_email}"
  "-var=oidc_jwks_url=${oidc_jwks_url}"
  "-var=oidc_issuer=${oidc_issuer}"
  "-var=oidc_audience=${oidc_audience}"
  "-var=policy_url=${policy_url}"
)

case "$operation" in
  plan) terraform -chdir="$root" plan -input=false "${vars[@]}" ;;
  apply-foundation)
    [[ "${enable_durable_database}" == "true" ]] || { echo "Foundation apply requires AGENTCONSTRUCT_ENABLE_DURABLE_DATABASE=true" >&2; exit 2; }
    [[ "${enable_service}" == "false" ]] || { echo "Foundation apply cannot enable the hosted service" >&2; exit 2; }
    [[ -n "${monitoring_email}" ]] || { echo "Set AGENTCONSTRUCT_ALERT_EMAIL for actionable budget and alarm notifications" >&2; exit 2; }
    [[ "${CONFIRM_RUNTIME_FOUNDATION_APPLY:-}" == "APPLY_AGENTCONSTRUCT_RUNTIME_FOUNDATION" ]] || {
      echo "Set CONFIRM_RUNTIME_FOUNDATION_APPLY=APPLY_AGENTCONSTRUCT_RUNTIME_FOUNDATION after reviewing the plan" >&2; exit 2;
    }
    terraform -chdir="$root" apply -input=false -auto-approve "${vars[@]}" ;;
  apply-service)
    [[ "${enable_service}" == "true" ]] || { echo "Set AGENTCONSTRUCT_ENABLE_RUNTIME_SERVICE=true" >&2; exit 2; }
    [[ "${image_identifier}" != "placeholder.invalid/agentconstruct:unset" ]] || { echo "Set AGENTCONSTRUCT_RUNTIME_IMAGE_IDENTIFIER" >&2; exit 2; }
    [[ "${enable_durable_database}" == "true" ]] || { echo "Hosted service requires the durable database" >&2; exit 2; }
    [[ "${oidc_jwks_url}" == https://* && "${oidc_issuer}" == https://* && -n "${oidc_audience}" ]] || {
      echo "Set the production AGENTCONSTRUCT_JWKS_URL, AGENTCONSTRUCT_OIDC_ISSUER and AGENTCONSTRUCT_OIDC_AUDIENCE" >&2; exit 2;
    }
    [[ "${policy_url}" == https://* ]] || { echo "Set an HTTPS AGENTCONSTRUCT_OPA_URL for the independent policy service" >&2; exit 2; }
    [[ "${CONFIRM_RUNTIME_SERVICE_APPLY:-}" == "APPLY_AGENTCONSTRUCT_RUNTIME_SERVICE" ]] || {
      echo "Set CONFIRM_RUNTIME_SERVICE_APPLY=APPLY_AGENTCONSTRUCT_RUNTIME_SERVICE after reviewing the plan" >&2; exit 2;
    }
    terraform -chdir="$root" apply -input=false -auto-approve "${vars[@]}" ;;
  destroy)
    [[ "${database_deletion_protection}" == "false" ]] || {
      echo "Set AGENTCONSTRUCT_DATABASE_DELETION_PROTECTION=false only after an approved final backup" >&2; exit 2;
    }
    [[ "${CONFIRM_RUNTIME_DESTROY:-}" == "DESTROY_AGENTCONSTRUCT_RUNTIME" ]] || {
      echo "Set CONFIRM_RUNTIME_DESTROY=DESTROY_AGENTCONSTRUCT_RUNTIME" >&2; exit 2;
    }
    terraform -chdir="$root" destroy -input=false -auto-approve "${vars[@]}" ;;
  output) terraform -chdir="$root" output -json ;;
  verify-absent)
    service_count="$(aws apprunner list-services "${aws_args[@]}" --region "$AWS_REGION" --query "length(ServiceSummaryList[?ServiceName=='agentconstruct-runtime'])" --output text)"
    database_count="$(aws rds describe-db-instances "${aws_args[@]}" --region "$AWS_REGION" --query "length(DBInstances[?DBInstanceIdentifier=='agentconstruct-runtime-postgres'])" --output text)"
    vpc_count="$(aws ec2 describe-vpcs "${aws_args[@]}" --region "$AWS_REGION" --filters "Name=tag:Scope,Values=platform" --query 'length(Vpcs)' --output text)"
    [[ "$service_count" == "0" && "$database_count" == "0" && "$vpc_count" == "0" ]] || {
      echo "Platform resources remain: service=${service_count}, database=${database_count}, vpc=${vpc_count}" >&2; exit 1;
    }
    echo "Platform runtime service, database and tagged VPC are absent"
    ;;
  *) echo "usage: $0 {plan|apply-foundation|apply-service|destroy|output|verify-absent}" >&2; exit 2 ;;
esac
