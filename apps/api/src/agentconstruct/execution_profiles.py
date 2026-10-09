"""Select a bounded delivery contract from the approved architecture profile."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionProfile:
    profile: str
    delivery_kind: str
    terraform_boundary: str
    gitops_boundary: str
    kubernetes_boundary: str


_PROFILES: dict[str, ExecutionProfile] = {
    "aws-s3-cloudfront-static": ExecutionProfile(
        "aws-s3-cloudfront-static", "static-hosting", "selected static Terraform contract", "not used", "not used"
    ),
    "aws-lambda-api": ExecutionProfile(
        "aws-lambda-api", "serverless", "selected Lambda/API Gateway Terraform contract", "not used", "not used"
    ),
    "aws-app-runner": ExecutionProfile(
        "aws-app-runner", "managed-application", "selected App Runner Terraform contract", "not used", "not used"
    ),
    "aws-ecs-fargate": ExecutionProfile(
        "aws-ecs-fargate", "managed-containers", "selected ECS Terraform contract", "optional reviewed desired state", "not used"
    ),
    "aws-ec2-managed": ExecutionProfile(
        "aws-ec2-managed", "managed-vm", "selected EC2 Terraform contract", "not used", "not used"
    ),
    "aws-managed-ai": ExecutionProfile(
        "aws-managed-ai", "managed-ai", "selected managed-AI Terraform contract", "not used", "not used"
    ),
    "aws-cpu-inference": ExecutionProfile(
        "aws-cpu-inference", "cpu-inference", "selected compute Terraform contract", "optional reviewed desired state", "not used"
    ),
    "aws-gpu-inference": ExecutionProfile(
        "aws-gpu-inference", "gpu-inference", "selected accelerator Terraform contract", "optional reviewed desired state", "not used"
    ),
    "aws-eks-governed": ExecutionProfile(
        "aws-eks-governed", "kubernetes", "selected EKS Terraform contract", "reviewed GitOps pull request and Argo observation", "required"
    ),
}


def execution_profile(profile: str) -> ExecutionProfile:
    try:
        return _PROFILES[profile]
    except KeyError as error:
        raise ValueError(f"no bounded execution contract exists for profile {profile}") from error
