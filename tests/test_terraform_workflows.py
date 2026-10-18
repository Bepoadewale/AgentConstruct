from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def workflow(name: str) -> str:
    return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


def test_serverless_plan_and_apply_are_manual_and_separate() -> None:
    plan = workflow("terraform-plan.yml")
    apply = workflow("terraform-apply.yml")

    assert "workflow_dispatch:" in plan
    assert "workflow_dispatch:" in apply
    assert "github.ref == 'refs/heads/main'" in plan
    assert "github.ref == 'refs/heads/main'" in apply
    assert "terraform plan -input=false -out=tfplan" in plan
    assert "terraform apply -input=false tfplan" in apply
    assert "terraform plan " not in apply
    assert "APPLY_SAVED_SERVERLESS_PLAN" in apply


def test_serverless_workflows_use_one_production_state() -> None:
    plan = workflow("terraform-plan.yml")
    apply = workflow("terraform-apply.yml")

    assert "options: [staging, production]" not in plan
    assert "inputs.environment" not in plan
    assert "TF_VAR_environment" not in plan
    assert 'key=serverless-control-plane/terraform.tfstate' in plan
    assert 'key=serverless-control-plane/terraform.tfstate' in apply
    assert '--arg deployment "production"' in plan
    assert "Unsupported saved-plan manifest" in apply
    assert "Saved plan is not for the production control plane" in apply


def test_serverless_terraform_uses_canonical_production_namespace() -> None:
    root = ROOT / "infrastructure" / "terraform" / "serverless-control-plane"
    variables = (root / "variables.tf").read_text(encoding="utf-8")
    main = (root / "main.tf").read_text(encoding="utf-8")

    assert 'variable "environment"' not in variables
    assert 'name = "agentconstruct"' in main
    assert 'Environment = "production"' in main
    assert "var.environment" not in main


def test_apply_verifies_exact_successful_saved_plan() -> None:
    apply = workflow("terraform-apply.yml")
    dispatch = apply.split("permissions:", maxsplit=1)[0]

    assert "plan_run_id" not in dispatch
    assert "plan_run_attempt" not in dispatch
    assert '"Terraform plan"' in apply
    assert '".github/workflows/terraform-plan.yml"' in apply
    assert '"workflow_dispatch"' in apply
    assert '"success"' in apply
    assert '"main"' in apply
    assert "actions/workflows/terraform-plan.yml/runs" in apply
    assert "select(.head_sha == $sha)" in apply
    assert "No manual Terraform plan exists for the current main commit" in apply
    assert 'test "${plan_sha}" = "${GITHUB_SHA}"' in apply
    assert "steps.plan_run.outputs.run_id" in apply
    assert "steps.plan_run.outputs.run_attempt" in apply
    assert "plan_run_attempt" in apply
    assert "manifest_version" in apply
    assert "production" in apply
    assert "sha256sum --check --strict" in apply
    assert "actions: read" in apply
    assert "environment: terraform-apply" in apply


def test_legacy_cloud_pilot_cannot_apply() -> None:
    pilot = workflow("cloud-pilot.yml")

    assert "options: [plan, destroy]" in pilot
    assert "APPLY_AGENTCONSTRUCT_PILOT" not in pilot
