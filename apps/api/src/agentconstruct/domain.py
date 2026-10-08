from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class EnvironmentName(StrEnum):
    STAGING = "staging"
    PRODUCTION = "production"


class LifecycleState(StrEnum):
    DRAFT = "DRAFT"
    ANALYZING = "ANALYZING"
    NEEDS_INPUT = "NEEDS_INPUT"
    PLANNED = "PLANNED"
    POLICY_DENIED = "POLICY_DENIED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    QUEUED = "QUEUED"
    PROVISIONING = "PROVISIONING"
    DEPLOYING = "DEPLOYING"
    VERIFYING = "VERIFYING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    DESTROY_REQUESTED = "DESTROY_REQUESTED"
    DESTROY_APPROVAL_REQUIRED = "DESTROY_APPROVAL_REQUIRED"
    DESTROYING = "DESTROYING"
    DESTROYED = "DESTROYED"


class PlanAction(StrEnum):
    DEPLOY = "DEPLOY"
    DESTROY = "DESTROY"


class PolicyResult(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class WorkloadSpec(BaseModel):
    workload_type: str
    source_repository: str | None = None
    cloud: str = "aws"
    data_classification: str = "unknown"
    average_rps: int | None = Field(default=None, ge=0)
    peak_rps: int | None = Field(default=None, ge=0)
    monthly_budget_usd: int | None = Field(default=None, ge=1)
    environments: list[EnvironmentName] = Field(default_factory=list)
    availability_target: str | None = None
    region_constraints: list[str] = Field(default_factory=list)
    model_requirements: dict[str, Any] = Field(default_factory=dict)
    integration_requirements: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    provenance: dict[str, str] = Field(default_factory=dict)


class MaterialQuestion(BaseModel):
    field: str
    question: str
    reason: str


class IntentInterpretation(BaseModel):
    spec: WorkloadSpec
    questions: list[MaterialQuestion] = Field(default_factory=list)


class ArchitectureComponent(BaseModel):
    name: str
    purpose: str
    service: str
    private: bool = True


class CostRange(BaseModel):
    currency: str = "USD"
    monthly_low: int
    monthly_high: int
    assumptions: list[str]
    catalog_version: str
    estimated_at: datetime


class ArchitecturePlan(BaseModel):
    profile: str
    cloud: str = "aws"
    region: str
    components: list[ArchitectureComponent]
    dependencies: list[str]
    assumptions: list[str]
    security_controls: list[str]
    cost_estimate: CostRange
    estimated_capacity: str
    risks: list[str]
    alternatives: list[str]
    operational_characteristics: list[str]
    rollback_strategy: str
    execution_steps: list[str]


class IntentRequest(BaseModel):
    project_id: str
    prompt: str = Field(min_length=20, max_length=10_000)
    source_repository: str | None = None
    cloud_connection_id: str | None = None
    idempotency_key: str = Field(min_length=8, max_length=128)


class ProjectRequest(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9-]{2,40}$")
    repository_url: HttpUrl | None = None


class CloudConnectionRequest(BaseModel):
    display_name: str = Field(min_length=3, max_length=100)
    provider: str = Field(default="aws", pattern=r"^aws$")
    connection_mode: str = Field(default="byoc_role_contract", pattern=r"^byoc_role_contract$")


class ApprovalRequest(BaseModel):
    plan_hash: str = Field(min_length=64, max_length=64)


class LocalLoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=80)
