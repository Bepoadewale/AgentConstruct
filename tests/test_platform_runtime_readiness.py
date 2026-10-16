from pathlib import Path

MAIN = Path("infrastructure/terraform/app-runner-runtime/main.tf").read_text(encoding="utf-8")
VARIABLES = Path("infrastructure/terraform/app-runner-runtime/variables.tf").read_text(
    encoding="utf-8"
)
RUNTIME_SCRIPT = Path("scripts/app-runner-runtime.sh").read_text(encoding="utf-8")
OPERATIONS_SCRIPT = Path("scripts/platform-runtime-operations.sh").read_text(encoding="utf-8")
NOVA_EVALUATION = Path("scripts/nova_live_evaluation.py").read_text(encoding="utf-8")


def test_hosted_service_requires_durable_data_identity_policy_and_image():
    assert "!var.enable_service || var.enable_durable_database" in MAIN
    assert 'can(regex("^https://", var.oidc_jwks_url))' in MAIN
    assert 'can(regex("^https://", var.policy_url))' in MAIN
    assert 'AGENTCONSTRUCT_POLICY_FIXTURE              = "false"' in MAIN
    assert "AGENTCONSTRUCT_JWKS_URL" in MAIN
    assert "AGENTCONSTRUCT_OPA_URL" in MAIN
    assert "Hosted service activation requires" in MAIN
    assert "production AGENTCONSTRUCT_JWKS_URL" in RUNTIME_SCRIPT


def test_platform_database_has_recovery_and_privacy_controls():
    for contract in (
        "storage_encrypted           = true",
        "publicly_accessible         = false",
        "skip_final_snapshot         = false",
        "deletion_protection         = var.database_deletion_protection",
        "backup_retention_period     = var.database_backup_retention_days",
        "copy_tags_to_snapshot       = true",
        "delete_automated_backups    = false",
    ):
        assert contract in MAIN
    assert "database_backup_retention_days >= 7" in VARIABLES


def test_idle_foundation_does_not_pay_for_an_unused_nat_gateway():
    assert "service_network_enabled = var.enable_durable_database && var.enable_service" in MAIN
    assert 'resource "aws_nat_gateway" "runtime"' in MAIN
    assert MAIN.count("count  = local.service_network_enabled ? 1 : 0") >= 4


def test_budget_and_actionable_alarm_contracts_exist():
    assert 'resource "aws_budgets_budget" "platform"' in MAIN
    assert 'values = ["user:Project$agentconstruct"]' in MAIN
    assert 'resource "aws_sns_topic" "platform_alerts"' in MAIN
    for alarm in ("database_cpu_high", "database_storage_low", "database_connections_high"):
        assert f'resource "aws_cloudwatch_metric_alarm" "{alarm}"' in MAIN
    assert 'resource "aws_cloudwatch_metric_alarm" "service_5xx"' in MAIN
    assert 'resource "aws_cloudwatch_metric_alarm" "service_latency"' in MAIN


def test_nova_evaluation_and_recovery_operations_are_bounded():
    assert "MAX_CASES = 2" in NOVA_EVALUATION
    assert "MAX_OUTPUT_TOKENS_PER_CASE = 384" in NOVA_EVALUATION
    assert '"raw_prompts_retained": False' in NOVA_EVALUATION
    assert '"raw_outputs_retained": False' in NOVA_EVALUATION
    assert "EXPECTED_AWS_ACCOUNT_ID" in NOVA_EVALUATION
    assert "RESTORE_AND_DELETE_AGENTCONSTRUCT_PLATFORM_DRILL" in OPERATIONS_SCRIPT
    assert "SNAPSHOT_AGENTCONSTRUCT_PLATFORM" in OPERATIONS_SCRIPT
    assert "--no-publicly-accessible" in OPERATIONS_SCRIPT
    assert "db-instance-deleted" in OPERATIONS_SCRIPT
