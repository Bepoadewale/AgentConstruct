from pathlib import Path

ROOT = Path("infrastructure/terraform/customer-connection")


def test_customer_discovery_role_has_only_read_actions_and_execution_role_has_no_policy():
    configuration = (ROOT / "main.tf").read_text()
    assert 'resource "aws_iam_role" "discovery"' in configuration
    assert 'resource "aws_iam_role" "execution_contract"' in configuration
    assert 'resource "aws_iam_role_policy" "discovery"' in configuration
    assert 'resources = ["*"]' in configuration
    assert "Create" not in configuration
    assert "Delete" not in configuration
    assert "Put" not in configuration
    assert "Update" not in configuration
    assert "secretsmanager:" not in configuration
    assert "GetSecretValue" not in configuration
    execution_section = configuration.split('resource "aws_iam_role" "execution_contract"', 1)[1]
    assert "aws_iam_role_policy" not in execution_section


def test_customer_connection_apply_and_destroy_require_explicit_confirmation():
    script = Path("scripts/customer-aws-connection.sh").read_text()
    assert "AWS account guard failed" in script
    assert "APPLY_AGENTCONSTRUCT_CUSTOMER_CONNECTION" in script
    assert "DESTROY_AGENTCONSTRUCT_CUSTOMER_CONNECTION" in script
    assert "agentconstruct/customer-connections/${CUSTOMER_CONNECTION_ID}.tfstate" in script


def test_quick_create_template_is_metadata_only_and_uses_external_id_trust():
    template = Path("infrastructure/cloudformation/customer-discovery-role.yaml").read_text()
    assert "AWS::IAM::Role" in template
    assert "sts:ExternalId" in template
    assert "secretsmanager:DescribeSecret" in template
    assert "secretsmanager:GetSecretValue" not in template
    assert "s3:GetObject" not in template
    assert "iam:PassRole" not in template
    assert ":Create" not in template
