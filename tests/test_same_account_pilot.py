from pathlib import Path

CUSTOMER_MAIN = Path(
    "infrastructure/terraform/customer-workload-app-runner-pilot/main.tf"
).read_text(encoding="utf-8")
CUSTOMER_VARIABLES = Path(
    "infrastructure/terraform/customer-workload-app-runner-pilot/variables.tf"
).read_text(encoding="utf-8")
CUSTOMER_OUTPUTS = Path(
    "infrastructure/terraform/customer-workload-app-runner-pilot/outputs.tf"
).read_text(encoding="utf-8")
CUSTOMER_SCRIPT = Path("scripts/customer-workload-app-runner-pilot.sh").read_text(
    encoding="utf-8"
)
PLATFORM_MAIN = Path("infrastructure/terraform/app-runner-runtime/main.tf").read_text(
    encoding="utf-8"
)
PLATFORM_SCRIPT = Path("scripts/app-runner-runtime.sh").read_text(encoding="utf-8")


def test_platform_and_customer_use_explicit_non_overlapping_placements():
    assert 'Scope           = "platform"' in PLATFORM_MAIN
    assert 'Placement       = "platform"' in PLATFORM_MAIN
    assert 'default     = "10.42.0.0/16"' in Path(
        "infrastructure/terraform/app-runner-runtime/variables.tf"
    ).read_text(encoding="utf-8")
    assert 'default     = "customer-sandbox"' in CUSTOMER_VARIABLES
    assert 'default     = "10.84.0.0/16"' in CUSTOMER_VARIABLES
    assert "var.customer_vpc_cidr != var.platform_vpc_cidr" in CUSTOMER_MAIN
    assert "SAME_ACCOUNT_PILOT_NOT_CROSS_ACCOUNT" in CUSTOMER_OUTPUTS


def test_customer_sandbox_has_a_dedicated_low_cost_vpc_boundary():
    assert 'resource "aws_vpc" "customer_sandbox"' in CUSTOMER_MAIN
    assert 'resource "aws_subnet" "customer_private"' in CUSTOMER_MAIN
    assert 'resource "aws_apprunner_vpc_connector" "customer_sandbox"' in CUSTOMER_MAIN
    assert 'egress_type       = "VPC"' in CUSTOMER_MAIN
    assert 'resource "aws_nat_gateway"' not in CUSTOMER_MAIN
    assert 'resource "aws_internet_gateway"' not in CUSTOMER_MAIN
    assert "davdeploy-customer-sandbox-apprunner-runtime" in CUSTOMER_MAIN


def test_state_and_teardown_are_scope_specific_and_account_guarded():
    assert "davdeploy/platform/app-runner-runtime.tfstate" in PLATFORM_SCRIPT
    assert "davdeploy/customer-sandbox/workload-app-runner.tfstate" in CUSTOMER_SCRIPT
    assert "EXPECTED_AWS_ACCOUNT_ID" in PLATFORM_SCRIPT
    assert "EXPECTED_AWS_ACCOUNT_ID" in CUSTOMER_SCRIPT
    assert "Customer sandbox VPC still exists" in CUSTOMER_SCRIPT
    assert "Customer sandbox IAM role still exists" in CUSTOMER_SCRIPT
    combined = CUSTOMER_MAIN + CUSTOMER_SCRIPT + PLATFORM_MAIN + PLATFORM_SCRIPT
    assert "organizations create-account" not in combined
    assert "organizations invite-account" not in combined
