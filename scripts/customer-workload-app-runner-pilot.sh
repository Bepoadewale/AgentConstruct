#!/usr/bin/env bash
set -euo pipefail

operation="${1:-}"
root="infrastructure/terraform/customer-workload-app-runner-pilot"

require() {
  local name="$1"
  [[ -n "${!name:-}" ]] || { echo "${name} is required" >&2; exit 2; }
}

require EXPECTED_AWS_ACCOUNT_ID
require TF_STATE_BUCKET
require TF_LOCK_TABLE
require AWS_REGION

service_name="${AGENTCONSTRUCT_CUSTOMER_SERVICE_NAME:-agentconstruct-customer-control-plane}"
repository_name="${AGENTCONSTRUCT_CUSTOMER_ECR_REPOSITORY_NAME:-agentconstruct-customer-ai-platform-control-plane}"
source_repository="${AGENTCONSTRUCT_CUSTOMER_SOURCE_REPOSITORY:-https://github.com/Bepoadewale/ai-platform-control-plane}"
source_commit="${AGENTCONSTRUCT_CUSTOMER_SOURCE_COMMIT:-unknown}"
plan_digest="${AGENTCONSTRUCT_CUSTOMER_PLAN_DIGEST:-customer-workload-pilot-local-approval}"
image_identifier="${AGENTCONSTRUCT_CUSTOMER_IMAGE_IDENTIFIER:-placeholder.invalid/agentconstruct-customer-workload:unset}"
enable_service="${AGENTCONSTRUCT_ENABLE_CUSTOMER_SERVICE:-false}"

aws_args=()
if [[ -n "${AWS_PROFILE:-}" ]]; then
  aws_args+=(--profile "$AWS_PROFILE")
fi

account="$(aws sts get-caller-identity "${aws_args[@]}" --query Account --output text)"
[[ "$account" == "$EXPECTED_AWS_ACCOUNT_ID" ]] || { echo "AWS account guard failed: got ${account}, expected ${EXPECTED_AWS_ACCOUNT_ID}" >&2; exit 3; }

tf_vars=(
  "-var=region=${AWS_REGION}"
  "-var=expected_account_id=${EXPECTED_AWS_ACCOUNT_ID}"
  "-var=service_name=${service_name}"
  "-var=ecr_repository_name=${repository_name}"
  "-var=source_repository=${source_repository}"
  "-var=source_commit=${source_commit}"
  "-var=plan_digest=${plan_digest}"
  "-var=image_identifier=${image_identifier}"
  "-var=enable_service=${enable_service}"
)

tf_init() {
  terraform -chdir="$root" init -input=false \
    -backend-config="bucket=${TF_STATE_BUCKET}" \
    -backend-config="key=agentconstruct/customer-workload-app-runner-pilot.tfstate" \
    -backend-config="dynamodb_table=${TF_LOCK_TABLE}" \
    -backend-config="region=${AWS_REGION}"
}

tf_output() {
  terraform -chdir="$root" output -json
}

service_arn() {
  terraform -chdir="$root" output -raw app_runner_service_arn
}

service_url() {
  terraform -chdir="$root" output -raw app_runner_service_url
}

case "$operation" in
  plan)
    tf_init
    terraform -chdir="$root" plan -input=false "${tf_vars[@]}"
    ;;
  apply-foundation)
    [[ "${CONFIRM_CUSTOMER_WORKLOAD_FOUNDATION_APPLY:-}" == "APPLY_CUSTOMER_WORKLOAD_FOUNDATION" ]] || {
      echo "Set CONFIRM_CUSTOMER_WORKLOAD_FOUNDATION_APPLY=APPLY_CUSTOMER_WORKLOAD_FOUNDATION after reviewing the plan" >&2; exit 2;
    }
    tf_init
    terraform -chdir="$root" apply -input=false -auto-approve "${tf_vars[@]}"
    ;;
  build-push-image)
    require AGENTCONSTRUCT_CUSTOMER_ECR_REPOSITORY_URL
    require AGENTCONSTRUCT_CUSTOMER_SOURCE_DIR
    tag="${AGENTCONSTRUCT_CUSTOMER_IMAGE_TAG:-$(date -u +%Y%m%d%H%M%S)}"
    repo="${AGENTCONSTRUCT_CUSTOMER_ECR_REPOSITORY_URL}"
    registry="${repo%%/*}"
    aws ecr get-login-password "${aws_args[@]}" --region "$AWS_REGION" | docker login --username AWS --password-stdin "$registry"
    docker buildx build \
      --platform linux/amd64 \
      --provenance=false \
      --sbom=false \
      --push \
      -t "${repo}:${tag}" \
      -f "${AGENTCONSTRUCT_CUSTOMER_SOURCE_DIR}/control-plane/Dockerfile" \
      "${AGENTCONSTRUCT_CUSTOMER_SOURCE_DIR}"
    printf '%s:%s\n' "$repo" "$tag"
    ;;
  apply-service)
    [[ "${enable_service}" == "true" ]] || { echo "Set AGENTCONSTRUCT_ENABLE_CUSTOMER_SERVICE=true" >&2; exit 2; }
    [[ "${image_identifier}" != "placeholder.invalid/agentconstruct-customer-workload:unset" ]] || { echo "Set AGENTCONSTRUCT_CUSTOMER_IMAGE_IDENTIFIER" >&2; exit 2; }
    [[ "${CONFIRM_CUSTOMER_WORKLOAD_SERVICE_APPLY:-}" == "APPLY_CUSTOMER_WORKLOAD_SERVICE" ]] || {
      echo "Set CONFIRM_CUSTOMER_WORKLOAD_SERVICE_APPLY=APPLY_CUSTOMER_WORKLOAD_SERVICE after reviewing the plan" >&2; exit 2;
    }
    tf_init
    terraform -chdir="$root" apply -input=false -auto-approve "${tf_vars[@]}"
    ;;
  wait-ready)
    tf_init
    arn="$(service_arn)"
    for _ in {1..90}; do
      status="$(aws apprunner describe-service "${aws_args[@]}" --service-arn "$arn" --query 'Service.Status' --output text)"
      echo "App Runner status: ${status}"
      [[ "$status" == "RUNNING" ]] && exit 0
      [[ "$status" == "CREATE_FAILED" || "$status" == "DELETE_FAILED" || "$status" == "OPERATION_IN_PROGRESS" || "$status" == "PAUSED" ]] || true
      sleep 10
    done
    echo "Timed out waiting for App Runner service to become RUNNING" >&2
    exit 1
    ;;
  smoke)
    tf_init
    url="$(service_url)"
    curl --fail --silent --show-error --max-time 15 "${url}/healthz" | jq -e '.status == "ok"' >/dev/null
    echo "Customer workload smoke passed: ${url}/healthz returned ok"
    ;;
  destroy)
    [[ "${CONFIRM_CUSTOMER_WORKLOAD_DESTROY:-}" == "DESTROY_CUSTOMER_WORKLOAD" ]] || {
      echo "Set CONFIRM_CUSTOMER_WORKLOAD_DESTROY=DESTROY_CUSTOMER_WORKLOAD" >&2; exit 2;
    }
    tf_init
    terraform -chdir="$root" destroy -input=false -auto-approve "${tf_vars[@]}"
    ;;
  verify-absent)
    missing_service="false"
    if aws apprunner list-services "${aws_args[@]}" --query "ServiceSummaryList[?ServiceName=='${service_name}'].ServiceArn | [0]" --output text | grep -qv '^None$'; then
      echo "App Runner service still exists: ${service_name}" >&2
      exit 1
    else
      missing_service="true"
    fi
    if aws ecr describe-repositories "${aws_args[@]}" --repository-names "$repository_name" >/dev/null 2>&1; then
      echo "ECR repository still exists: ${repository_name}" >&2
      exit 1
    fi
    echo "Customer workload AWS resources absent: service=${missing_service}, ecr_repository=deleted"
    ;;
  output)
    tf_init
    tf_output
    ;;
  *)
    echo "usage: $0 {plan|apply-foundation|build-push-image|apply-service|wait-ready|smoke|destroy|verify-absent|output}" >&2
    exit 2
    ;;
esac
