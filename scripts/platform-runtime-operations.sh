#!/usr/bin/env bash
set -euo pipefail

operation="${1:-}"
database_id="agentconstruct-runtime-postgres"
service_name="agentconstruct-runtime"
budget_name="agentconstruct-platform-monthly"
snapshot_id="${AGENTCONSTRUCT_PLATFORM_SNAPSHOT_ID:-}"
restore_id="${AGENTCONSTRUCT_PLATFORM_RESTORE_ID:-agentconstruct-runtime-restore-drill}"

require() {
  local name="$1"
  [[ -n "${!name:-}" ]] || { echo "${name} is required" >&2; exit 2; }
}

require EXPECTED_AWS_ACCOUNT_ID
require AWS_REGION
[[ "${AGENTCONSTRUCT_PLATFORM_SCOPE:-platform}" == "platform" ]] || { echo "Platform scope guard failed" >&2; exit 3; }

aws_args=()
if [[ -n "${AWS_PROFILE:-}" ]]; then
  aws_args+=(--profile "$AWS_PROFILE")
fi
account="$(aws sts get-caller-identity "${aws_args[@]}" --query Account --output text)"
[[ "$account" == "$EXPECTED_AWS_ACCOUNT_ID" ]] || { echo "AWS account guard failed: got ${account}, expected ${EXPECTED_AWS_ACCOUNT_ID}" >&2; exit 3; }

verify_foundation() {
  local database
  database="$(aws rds describe-db-instances "${aws_args[@]}" --region "$AWS_REGION" --db-instance-identifier "$database_id" --query 'DBInstances[0].[DBInstanceStatus,StorageEncrypted,PubliclyAccessible,BackupRetentionPeriod,DeletionProtection]' --output text)"
  read -r status encrypted public backup_retention deletion_protection <<<"$database"
  [[ "$status" == "available" && "$encrypted" == "True" && "$public" == "False" ]] || { echo "Database readiness or privacy check failed: ${database}" >&2; exit 1; }
  (( backup_retention >= 7 )) || { echo "Database backup retention is below seven days" >&2; exit 1; }
  [[ "$deletion_protection" == "True" ]] || { echo "Database deletion protection is disabled" >&2; exit 1; }
  vpc_count="$(aws ec2 describe-vpcs "${aws_args[@]}" --region "$AWS_REGION" --filters "Name=tag:Scope,Values=platform" --query 'length(Vpcs)' --output text)"
  [[ "$vpc_count" == "1" ]] || { echo "Expected one tagged platform VPC, found ${vpc_count}" >&2; exit 1; }
  alarm_count="$(aws cloudwatch describe-alarms "${aws_args[@]}" --region "$AWS_REGION" --alarm-name-prefix agentconstruct-platform-rds- --query 'length(MetricAlarms)' --output text)"
  (( alarm_count >= 3 )) || { echo "Expected three database alarms, found ${alarm_count}" >&2; exit 1; }
  aws budgets describe-budget "${aws_args[@]}" --account-id "$account" --budget-name "$budget_name" >/dev/null
  aws bedrock get-inference-profile "${aws_args[@]}" --region "$AWS_REGION" --inference-profile-identifier us.amazon.nova-2-lite-v1:0 >/dev/null
  echo "Platform foundation verified: database=available, encrypted=true, public=false, backups=${backup_retention}d, deletion_protection=true, alarms=${alarm_count}, vpc=${vpc_count}, budget=${budget_name}, nova=active"
}

cleanup_restore() {
  if aws rds describe-db-instances "${aws_args[@]}" --region "$AWS_REGION" --db-instance-identifier "$restore_id" >/dev/null 2>&1; then
    aws rds delete-db-instance "${aws_args[@]}" --region "$AWS_REGION" --db-instance-identifier "$restore_id" --skip-final-snapshot --delete-automated-backups >/dev/null || true
  fi
}

case "$operation" in
  verify-foundation)
    verify_foundation
    ;;
  verify-service)
    verify_foundation
    service_arn="$(aws apprunner list-services "${aws_args[@]}" --region "$AWS_REGION" --query "ServiceSummaryList[?ServiceName=='${service_name}'].ServiceArn | [0]" --output text)"
    [[ -n "$service_arn" && "$service_arn" != "None" ]] || { echo "Hosted service is absent" >&2; exit 1; }
    read -r service_status service_url <<<"$(aws apprunner describe-service "${aws_args[@]}" --region "$AWS_REGION" --service-arn "$service_arn" --query 'Service.[Status,ServiceUrl]' --output text)"
    [[ "$service_status" == "RUNNING" ]] || { echo "Hosted service is not RUNNING: ${service_status}" >&2; exit 1; }
    curl --fail --silent --show-error --max-time 15 "https://${service_url}/healthz" >/dev/null
    echo "Hosted service verified: status=RUNNING, TLS health endpoint=ok"
    ;;
  snapshot)
    require AGENTCONSTRUCT_PLATFORM_SNAPSHOT_ID
    [[ "$snapshot_id" == agentconstruct-runtime-manual-* ]] || { echo "Snapshot ID must start with agentconstruct-runtime-manual-" >&2; exit 2; }
    [[ "${CONFIRM_PLATFORM_SNAPSHOT:-}" == "SNAPSHOT_AGENTCONSTRUCT_PLATFORM" ]] || { echo "Set CONFIRM_PLATFORM_SNAPSHOT=SNAPSHOT_AGENTCONSTRUCT_PLATFORM" >&2; exit 2; }
    verify_foundation
    aws rds create-db-snapshot "${aws_args[@]}" --region "$AWS_REGION" --db-instance-identifier "$database_id" --db-snapshot-identifier "$snapshot_id" --tags Key=Project,Value=agentconstruct Key=Scope,Value=platform Key=Purpose,Value=restore-drill >/dev/null
    aws rds wait db-snapshot-available "${aws_args[@]}" --region "$AWS_REGION" --db-snapshot-identifier "$snapshot_id"
    aws rds describe-db-snapshots "${aws_args[@]}" --region "$AWS_REGION" --db-snapshot-identifier "$snapshot_id" --query 'DBSnapshots[0].[Status,Encrypted,DBInstanceIdentifier]' --output text
    ;;
  restore-drill)
    require AGENTCONSTRUCT_PLATFORM_SNAPSHOT_ID
    [[ "$snapshot_id" == agentconstruct-runtime-manual-* ]] || { echo "Snapshot ID must start with agentconstruct-runtime-manual-" >&2; exit 2; }
    [[ "$restore_id" == "agentconstruct-runtime-restore-drill" ]] || { echo "Restore drill target guard failed" >&2; exit 2; }
    [[ "${CONFIRM_PLATFORM_RESTORE_DRILL:-}" == "RESTORE_AND_DELETE_AGENTCONSTRUCT_PLATFORM_DRILL" ]] || { echo "Set CONFIRM_PLATFORM_RESTORE_DRILL=RESTORE_AND_DELETE_AGENTCONSTRUCT_PLATFORM_DRILL" >&2; exit 2; }
    subnet_group="$(aws rds describe-db-instances "${aws_args[@]}" --region "$AWS_REGION" --db-instance-identifier "$database_id" --query 'DBInstances[0].DBSubnetGroup.DBSubnetGroupName' --output text)"
    security_group="$(aws rds describe-db-instances "${aws_args[@]}" --region "$AWS_REGION" --db-instance-identifier "$database_id" --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' --output text)"
    trap cleanup_restore EXIT
    aws rds restore-db-instance-from-db-snapshot "${aws_args[@]}" --region "$AWS_REGION" --db-instance-identifier "$restore_id" --db-snapshot-identifier "$snapshot_id" --db-instance-class db.t4g.micro --db-subnet-group-name "$subnet_group" --vpc-security-group-ids "$security_group" --no-publicly-accessible --no-multi-az --no-deletion-protection --tags Key=Project,Value=agentconstruct Key=Scope,Value=platform Key=Purpose,Value=restore-drill >/dev/null
    aws rds wait db-instance-available "${aws_args[@]}" --region "$AWS_REGION" --db-instance-identifier "$restore_id"
    restored="$(aws rds describe-db-instances "${aws_args[@]}" --region "$AWS_REGION" --db-instance-identifier "$restore_id" --query 'DBInstances[0].[DBInstanceStatus,StorageEncrypted,PubliclyAccessible]' --output text)"
    [[ "$restored" == $'available\tTrue\tFalse' ]] || { echo "Restored database verification failed: ${restored}" >&2; exit 1; }
    aws rds delete-db-instance "${aws_args[@]}" --region "$AWS_REGION" --db-instance-identifier "$restore_id" --skip-final-snapshot --delete-automated-backups >/dev/null
    aws rds wait db-instance-deleted "${aws_args[@]}" --region "$AWS_REGION" --db-instance-identifier "$restore_id"
    trap - EXIT
    echo "Restore drill passed: snapshot restored encrypted/private and temporary database deleted. Application-level row verification was not possible before hosted identity activation."
    ;;
  *)
    echo "usage: $0 {verify-foundation|verify-service|snapshot|restore-drill}" >&2
    exit 2
    ;;
esac
