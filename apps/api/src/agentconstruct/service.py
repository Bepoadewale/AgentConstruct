from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentconstruct.domain import (
    EnvironmentName,
    LifecycleState,
    PlanAction,
    PolicyResult,
    WorkloadSpec,
)
from agentconstruct.executor import FixtureExecutor
from agentconstruct.intent import DeterministicIntentProvider, IntentProvider
from agentconstruct.models import (
    Approval,
    AuditEvent,
    DeploymentPlan,
    Environment,
    ExecutionJob,
    Organization,
    ProductUser,
    Project,
    StoredArchitecturePlan,
    WorkloadIntent,
)
from agentconstruct.planner import AwsV1Planner
from agentconstruct.policy import PolicyClient
from agentconstruct.security import Principal
from agentconstruct.state import require_transition


def plan_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ProductService:
    def __init__(self, db: Session, policy: PolicyClient | None = None, executor: FixtureExecutor | None = None, intent_provider: IntentProvider | None = None):
        self.db = db
        self.intent_provider = intent_provider or DeterministicIntentProvider()
        self.planner = AwsV1Planner()
        self.policy = policy or PolicyClient()
        self.executor = executor or FixtureExecutor()

    def seed_local_identity(self) -> None:
        for org_id, name in (("org-demo", "Demo AI Startup"), ("org-other", "Other Tenant")):
            if not self.db.get(Organization, org_id):
                self.db.add(Organization(id=org_id, name=name))
        users = [("user-founder", "org-demo", "developer"), ("user-operator", "org-demo", "operator"), ("user-other", "org-other", "developer")]
        for subject, org_id, role in users:
            if not self.db.scalar(select(ProductUser).where(ProductUser.subject == subject)):
                self.db.add(ProductUser(id=subject, organization_id=org_id, subject=subject, role=role))
        self.db.commit()

    def audit(self, principal: Principal, action: str, entity_type: str, entity_id: str, detail: dict) -> None:
        self.db.add(AuditEvent(organization_id=principal.organization_id, actor_subject=principal.subject, action=action, entity_type=entity_type, entity_id=entity_id, detail=detail))

    def create_project(self, principal: Principal, name: str, repository_url: str | None) -> Project:
        project = Project(organization_id=principal.organization_id, name=name, repository_url=repository_url)
        self.db.add(project)
        self.db.flush()
        self.audit(principal, "project.created", "project", project.id, {"name": name})
        self.db.commit()
        return project

    def _project(self, principal: Principal, project_id: str) -> Project:
        project = self.db.get(Project, project_id)
        if not project or project.organization_id != principal.organization_id:
            raise PermissionError("project not found in this organization")
        return project

    def create_intent(self, principal: Principal, project_id: str, prompt: str, source_repository: str | None, idempotency_key: str) -> WorkloadIntent:
        project = self._project(principal, project_id)
        existing = self.db.scalar(select(WorkloadIntent).where(WorkloadIntent.organization_id == principal.organization_id, WorkloadIntent.idempotency_key == idempotency_key))
        if existing:
            if existing.prompt != prompt or existing.project_id != project_id:
                raise ValueError("idempotency key conflicts with a different request")
            return existing
        selected_repository = source_repository or project.repository_url
        interpretation = self.intent_provider.interpret(prompt, selected_repository)
        spec = interpretation.spec
        state = LifecycleState.NEEDS_INPUT if spec.unknowns else LifecycleState.PLANNED
        intent = WorkloadIntent(organization_id=principal.organization_id, project_id=project.id, requester_subject=principal.subject, prompt=prompt, idempotency_key=idempotency_key, state=state, spec={**spec.model_dump(mode="json"), "questions": [question.model_dump() for question in interpretation.questions]})
        self.db.add(intent)
        self.db.flush()
        self.audit(principal, "intent.interpreted", "workload_intent", intent.id, {"state": state, "unknowns": spec.unknowns})
        self.db.commit()
        return intent

    def _intent(self, principal: Principal, intent_id: str) -> WorkloadIntent:
        intent = self.db.get(WorkloadIntent, intent_id)
        if not intent or intent.organization_id != principal.organization_id:
            raise PermissionError("intent not found in this organization")
        return intent

    def plan_intent(self, principal: Principal, intent_id: str) -> DeploymentPlan:
        intent = self._intent(principal, intent_id)
        spec = WorkloadSpec.model_validate(intent.spec)
        if spec.unknowns:
            raise ValueError(f"missing material requirements: {', '.join(spec.unknowns)}")
        architecture = self.planner.plan(spec)
        stored = self.db.scalar(select(StoredArchitecturePlan).where(StoredArchitecturePlan.intent_id == intent.id))
        if not stored:
            stored = StoredArchitecturePlan(organization_id=principal.organization_id, intent_id=intent.id, plan=architecture.model_dump(mode="json"))
            self.db.add(stored)
        decision = self.policy.evaluate(principal, spec, PlanAction.DEPLOY)
        payload = {"action": PlanAction.DEPLOY, "intent_id": intent.id, "spec": spec.model_dump(mode="json"), "architecture": architecture.model_dump(mode="json"), "policy": {"result": decision.result, "reason": decision.reason}}
        digest = plan_hash(payload)
        existing = self.db.scalar(select(DeploymentPlan).where(DeploymentPlan.plan_hash == digest))
        if existing:
            return existing
        state = {PolicyResult.ALLOW: LifecycleState.PLANNED, PolicyResult.DENY: LifecycleState.POLICY_DENIED, PolicyResult.APPROVAL_REQUIRED: LifecycleState.APPROVAL_REQUIRED}[decision.result]
        plan = DeploymentPlan(organization_id=principal.organization_id, intent_id=intent.id, requester_subject=principal.subject, action=PlanAction.DEPLOY, state=state, plan_hash=digest, policy_result=decision.result, payload=payload)
        self.db.add(plan)
        intent.state = state
        self.db.flush()
        self.audit(principal, "deployment_plan.created", "deployment_plan", plan.id, {"hash": digest, "policy": decision.result, "reason": decision.reason})
        self.db.commit()
        return plan

    def _plan(self, principal: Principal, plan_id: str) -> DeploymentPlan:
        plan = self.db.get(DeploymentPlan, plan_id)
        if not plan or plan.organization_id != principal.organization_id:
            raise PermissionError("deployment plan not found in this organization")
        return plan

    def approve(self, principal: Principal, plan_id: str, provided_hash: str) -> DeploymentPlan:
        plan = self._plan(principal, plan_id)
        if principal.role != "operator":
            raise PermissionError("operator role required for approval")
        if plan.requester_subject == principal.subject:
            raise PermissionError("requester cannot approve their own protected plan")
        if plan.plan_hash != provided_hash:
            raise ValueError("stale approval: plan hash changed")
        if plan.state not in {LifecycleState.APPROVAL_REQUIRED, LifecycleState.DESTROY_APPROVAL_REQUIRED}:
            raise ValueError("plan does not need approval")
        plan.state = LifecycleState.APPROVED
        self.db.add(Approval(deployment_plan_id=plan.id, plan_hash=plan.plan_hash, approver_subject=principal.subject))
        self.audit(principal, "deployment_plan.approved", "deployment_plan", plan.id, {"hash": plan.plan_hash})
        self.db.commit()
        return plan

    def execute(self, principal: Principal, plan_id: str) -> list[Environment]:
        plan = self._plan(principal, plan_id)
        if plan.action == PlanAction.DESTROY:
            return [self._execute_destroy(principal, plan)]
        if plan.state not in {LifecycleState.PLANNED, LifecycleState.APPROVED}:
            raise ValueError("plan is not executable")
        if plan.state == LifecycleState.APPROVED and not self.db.scalar(select(Approval).where(Approval.deployment_plan_id == plan.id, Approval.plan_hash == plan.plan_hash)):
            raise ValueError("approved plan has no matching durable approval")
        spec = WorkloadSpec.model_validate(plan.payload["spec"])
        environments = []
        plan.state = LifecycleState.QUEUED
        for environment_type in spec.environments:
            environment = Environment(organization_id=principal.organization_id, project_id=self._intent(principal, plan.intent_id).project_id, name=f"{self._intent(principal, plan.intent_id).id[:8]}-{environment_type}", environment_type=environment_type, state=LifecycleState.QUEUED, desired_state={"profile": plan.payload["architecture"]["profile"], "plan_hash": plan.plan_hash}, observed_state={})
            self.db.add(environment)
            self.db.flush()
            self.db.add(ExecutionJob(deployment_plan_id=plan.id, state=LifecycleState.QUEUED, result={"environment_id": environment.id}))
            for state in (LifecycleState.PROVISIONING, LifecycleState.DEPLOYING, LifecycleState.VERIFYING):
                require_transition(LifecycleState(environment.state), state)
                environment.state = state
            observation = self.executor.deploy(environment.id, should_fail="force failure" in self._intent(principal, plan.intent_id).prompt.lower())
            environment.observed_state = observation.detail
            target = LifecycleState.READY if observation.state == "READY" else LifecycleState.FAILED
            require_transition(LifecycleState(environment.state), target)
            environment.state = target
            self.audit(principal, "environment.observed", "environment", environment.id, {"state": target, "observation": observation.detail})
            environments.append(environment)
        self.db.commit()
        return environments

    def destroy_plan(self, principal: Principal, environment_id: str) -> DeploymentPlan:
        environment = self._environment(principal, environment_id)
        if LifecycleState(environment.state) not in {LifecycleState.READY, LifecycleState.FAILED, LifecycleState.DEGRADED}:
            raise ValueError("environment cannot be destroyed in its current state")
        environment.state = LifecycleState.DESTROY_REQUESTED
        requires_approval = environment.environment_type == EnvironmentName.PRODUCTION
        payload = {"action": PlanAction.DESTROY, "environment_id": environment.id, "observed_state": environment.observed_state}
        digest = plan_hash(payload)
        plan = DeploymentPlan(organization_id=principal.organization_id, environment_id=environment.id, requester_subject=principal.subject, action=PlanAction.DESTROY, state=LifecycleState.DESTROY_APPROVAL_REQUIRED if requires_approval else LifecycleState.PLANNED, plan_hash=digest, policy_result=PolicyResult.APPROVAL_REQUIRED if requires_approval else PolicyResult.ALLOW, payload=payload)
        self.db.add(plan)
        self.db.flush()
        self.audit(principal, "destroy_plan.created", "deployment_plan", plan.id, {"hash": digest, "approval_required": requires_approval})
        self.db.commit()
        return plan

    def _execute_destroy(self, principal: Principal, plan: DeploymentPlan) -> Environment:
        if plan.state not in {LifecycleState.PLANNED, LifecycleState.APPROVED}:
            raise ValueError("destroy plan is not executable")
        environment = self._environment(principal, plan.environment_id)
        environment.state = LifecycleState.DESTROYING
        observation = self.executor.destroy(environment.id)
        environment.observed_state = observation.detail
        environment.state = LifecycleState.DESTROYED if observation.state == "DESTROYED" else LifecycleState.FAILED
        self.audit(principal, "environment.destroyed" if environment.state == LifecycleState.DESTROYED else "environment.destroy_failed", "environment", environment.id, {"observation": observation.detail})
        self.db.commit()
        return environment

    def _environment(self, principal: Principal, environment_id: str) -> Environment:
        environment = self.db.get(Environment, environment_id)
        if not environment or environment.organization_id != principal.organization_id:
            raise PermissionError("environment not found in this organization")
        return environment

    def audits(self, principal: Principal) -> list[AuditEvent]:
        return list(self.db.scalars(select(AuditEvent).where(AuditEvent.organization_id == principal.organization_id).order_by(AuditEvent.created_at)))
