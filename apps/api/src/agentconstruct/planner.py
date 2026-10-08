from __future__ import annotations

from datetime import UTC, datetime

from agentconstruct.domain import ArchitectureComponent, ArchitecturePlan, CostRange, WorkloadSpec


class AwsV1Planner:
    """Small, explainable AWS catalogue; it does not generate unconstrained cloud designs."""

    catalog_version = "aws-v1-fixture-2026-10"

    def plan(self, spec: WorkloadSpec) -> ArchitecturePlan:
        if spec.cloud != "aws":
            raise ValueError("V1 supports AWS only")
        if spec.peak_rps is None or spec.monthly_budget_usd is None:
            raise ValueError("peak_rps and monthly_budget_usd are needed before architecture planning")
        high_scale = spec.peak_rps > 50
        profile = "aws-eks-governed" if high_scale else "aws-container-governed"
        base_low, base_high = (620, 1180) if high_scale else (280, 620)
        components = [
            ArchitectureComponent(name="application", purpose="Run the customer AI API", service="EKS" if high_scale else "ECS Fargate"),
            ArchitectureComponent(name="database", purpose="Durable application state", service="RDS PostgreSQL"),
            ArchitectureComponent(name="secrets", purpose="Store runtime references", service="AWS Secrets Manager"),
            ArchitectureComponent(name="telemetry", purpose="Measure health and cost evidence", service="OpenTelemetry + Prometheus + Grafana"),
        ]
        if spec.workload_type == "rag_application":
            components.append(ArchitectureComponent(name="documents", purpose="Store approved source artifacts", service="S3"))
        assumptions = [
            "Estimate uses a small transparent AWS fixture catalogue, not live billing data.",
            "Application and data remain private in the customer's AWS account.",
            "The estimate excludes model-provider token charges unless a provider price is supplied.",
        ]
        risks = []
        if spec.data_classification == "restricted":
            risks.append("Restricted data requires a reviewed data-retention and network policy before deployment.")
        if spec.monthly_budget_usd < base_low:
            risks.append("The requested budget is below the smallest recommended profile.")
        return ArchitecturePlan(
            profile=profile,
            region=spec.region_constraints[0] if spec.region_constraints else "us-east-1",
            components=components,
            dependencies=["customer AWS account", "GitHub repository connection", "scoped AWS role"],
            assumptions=assumptions,
            security_controls=["private networking", "least-privilege workload identity", "encrypted storage", "secret references only", "reviewed GitOps change"],
            cost_estimate=CostRange(
                monthly_low=base_low,
                monthly_high=base_high,
                assumptions=["us-east-1", "CPU-first profile", "two environments", "estimated infrastructure only"],
                catalog_version=self.catalog_version,
                estimated_at=datetime.now(UTC),
            ),
            estimated_capacity=f"Designed for {spec.average_rps or 0} average RPS and {spec.peak_rps} peak RPS with bounded autoscaling.",
            risks=risks,
            alternatives=["Use a smaller ECS profile for lower traffic.", "Use EKS when workload controls and scaling needs justify it."],
            operational_characteristics=["staging and production are isolated", "health is observed before READY", "destroy is governed"],
            rollback_strategy="Keep the prior approved desired state; revert through a reviewed GitOps change and observe recovery.",
            execution_steps=["validate cloud connection", "render reviewed desired state", "await approval", "run bounded executor", "observe health"],
        )
