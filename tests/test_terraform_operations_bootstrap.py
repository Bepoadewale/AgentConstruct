from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "infrastructure" / "terraform" / "terraform-operations-bootstrap"


def bootstrap_source() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(BOOTSTRAP.glob("*.tf"))
    )


def test_bootstrap_reuses_existing_state_lock_and_oidc_provider() -> None:
    source = bootstrap_source()

    assert 'data "aws_s3_bucket" "state"' in source
    assert 'data "aws_dynamodb_table" "lock"' in source
    assert 'data "aws_iam_openid_connect_provider" "github"' in source
    assert 'resource "aws_iam_openid_connect_provider"' not in source


def test_bootstrap_separates_plan_and_apply_trust() -> None:
    source = bootstrap_source()

    assert "repo:${var.github_repository}:environment:terraform-plan" in source
    assert "repo:${var.github_repository}:environment:terraform-apply" in source
    assert "sts:AssumeRoleWithWebIdentity" in source
    assert "AdministratorAccess" not in source
    assert "PowerUserAccess" not in source


def test_bootstrap_encrypts_and_expires_operational_artifacts() -> None:
    source = bootstrap_source()

    assert source.count('sse_algorithm     = "aws:kms"') == 2
    assert source.count("enable_key_rotation     = true") == 2
    assert 'resource "aws_s3_bucket_public_access_block" "plans"' in source
    assert 'resource "aws_s3_bucket_public_access_block" "releases"' in source
    assert "plan_retention_days" in source
    assert "release_retention_days" in source


def test_apply_role_is_limited_to_required_control_plane_services() -> None:
    source = bootstrap_source()

    assert 'resources = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/agentconstruct-*"]' in source
    assert 'resources = ["arn:${data.aws_partition.current.partition}:lambda:${var.region}:${data.aws_caller_identity.current.account_id}:function:agentconstruct-*"]' in source
    assert 'actions   = ["iam:CreateServiceLinkedRole"]' in source
    assert 'values   = ["rds.amazonaws.com"]' in source


def test_plan_workflow_uses_environment_specific_cognito_domain() -> None:
    workflow = (ROOT / ".github" / "workflows" / "terraform-plan.yml").read_text(
        encoding="utf-8"
    )

    assert "format('{0}-{1}', vars.COGNITO_DOMAIN_PREFIX, inputs.environment)" in workflow
