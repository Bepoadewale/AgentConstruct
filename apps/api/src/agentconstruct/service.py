from __future__ import annotations

import hashlib
import json
from typing import Any

from opentelemetry import trace
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
    CloudConnection,
    DeploymentPlan,
    Environment,
    ExecutionJob,
    Organization,
    ProductUser,
    Project,
    RepositoryConnection,
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

    def _trace(self, name: str):
        return trace.get_tracer("agentconstruct.product").start_as_current_span(name)

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
        if repository_url:
            self.db.add(
                RepositoryConnection(
                    organization_id=principal.organization_id,
                    project_id=project.id,
                    provider="github",
                    repository_url=repository_url,
                )
            )
        self.audit(principal, "project.created", "project", project.id, {"name": name})
        self.db.commit()
        return project

    def create_cloud_connection(self, principal: Principal, display_name: str, provider: str, connection_mode: str) -> CloudConnection:
        connection = CloudConnection(organization_id=principal.organization_id, display_name=display_name, provider=provider, connection_mode=connection_mode)
        self.db.add(connection)
        self.db.flush()
        self.audit(principal, "cloud_connection.created", "cloud_connection", connection.id, {"provider": provider, "mode": connection_mode})
        self.db.commit()
        return connection

    def cloud_connections(self, principal: Principal) -> list[CloudConnection]:
        return list(self.db.scalars(select(CloudConnection).where(CloudConnection.organization_id == principal.organization_id).order_by(CloudConnection.created_at)))

    def _project(self, principal: Principal, project_id: str) -> Project:
        project = self.db.get(Project, project_id)
        if not project or project.organization_id != principal.organization_id:
            raise PermissionError("project not found in this organization")
        return project

    def create_intent(
        self,
        principal: Principal,
        project_id: str,
        prompt: str,
        source_repository: str | None,
        cloud_connection_id: str | None,
        idempotency_key: str,
    ) -> WorkloadIntent:
        with self._trace("agentconstruct.intent.interpret") as span:
            span.set_attribute("agentconstruct.organization_id", principal.organization_id)
            return self._create_intent(principal, project_id, prompt, source_repository, cloud_connection_id, idempotency_key)

    def _create_intent(
        self, principal: Principal, project_id: str, prompt: str, source_repository: str | None,
        cloud_connection_id: str | None, idempotency_key: str,
    ) -> WorkloadIntent:
        project = self._project(principal, project_id)
        if cloud_connection_id:
            connection = self.db.get(CloudConnection, cloud_connection_id)
            if not connection or connection.organization_id != principal.organization_id:
                raise PermissionError("cloud connection not found in this organization")
        existing = self.db.scalar(select(WorkloadIntent).where(WorkloadIntent.organization_id == principal.organization_id, WorkloadIntent.idempotency_key == idempotency_key))
        if existing:
            if existing.prompt != prompt or existing.project_id != project_id:
                raise ValueError("idempotency key conflicts with a different request")
            return existing
        selected_repository = source_repository or project.repository_url
        interpretation = self.intent_provider.interpret(prompt, selected_repository)
        spec = interpretation.spec
        state = LifecycleState.NEEDS_INPUT if spec.unknowns else LifecycleState.PLANNED
        intent = WorkloadIntent(organization_id=principal.organization_id, project_id=project.id, requester_subject=principal.subject, prompt=prompt, idempotency_key=idempotency_key, state=state, spec={**spec.model_dump(mode="json"), "cloud_connection_id": cloud_connection_id, "questions": [question.model_dump() for question in interpretation.questions]})
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
        with self._trace("agentconstruct.architecture.plan"):
            return self._plan_intent(principal, intent_id)

    def _plan_intent(self, principal: Principal, intent_id: str) -> DeploymentPlan:
        intent = self._intent(principal, intent_id)
        spec = WorkloadSpec.model_validate(intent.spec)
        if spec.unknowns:
            raise ValueError(f"missing material requirements: {', '.join(spec.unknowns)}")
        architecture = self.planner.plan(spec)
        stored = self.db.scalar(select(StoredArchitecturePlan).where(StoredArchitecturePlan.intent_id == intent.id))
        if not stored:
            stored = StoredArchitecturePlan(organization_id=principal.organization_id, intent_id=intent.id, plan=architecture.model_dump(mode="json"))
            self.db.add(stored)
        with self._trace("agentconstruct.policy.evaluate"):
            decision = self.policy.evaluate(principal, spec, PlanAction.DEPLOY)
        payload = {
            "action": PlanAction.DEPLOY,
            "intent_id": intent.id,
            "cloud_connection_id": intent.spec.get("cloud_connection_id"),
            "spec": spec.model_dump(mode="json"),
            "architecture": architecture.model_dump(mode="json"),
            "policy": {"result": decision.result, "reason": decision.reason},
        }
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
        with self._trace("agentconstruct.plan.approve"):
            return self._approve(principal, plan_id, provided_hash)

    def _approve(self, principal: Principal, plan_id: str, provided_hash: str) -> DeploymentPlan:
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
        """Queue bounded work. A separate worker observes the fixture result."""
        plan = self._plan(principal, plan_id)
        if plan.action == PlanAction.DESTROY:
            return [self._queue_destroy(principal, plan)]
        if plan.state not in {LifecycleState.PLANNED, LifecycleState.APPROVED}:
            raise ValueError("plan is not executable")
        if plan.state == LifecycleState.APPROVED and not self.db.scalar(select(Approval).where(Approval.deployment_plan_id == plan.id, Approval.plan_hash == plan.plan_hash)):
            raise ValueError("approved plan has no matching durable approval")
        spec = WorkloadSpec.model_validate(plan.payload["spec"])
        environments: list[Environment] = []
        plan.state = LifecycleState.QUEUED
        intent = self._intent(principal, plan.intent_id)
        for environment_type in spec.environments:
            environment = Environment(organization_id=principal.organization_id, project_id=intent.project_id, name=f"{intent.id[:8]}-{environment_type}", environment_type=environment_type, state=LifecycleState.QUEUED, desired_state={"profile": plan.payload["architecture"]["profile"], "plan_hash": plan.plan_hash, "should_fail": "force failure" in intent.prompt.lower()}, observed_state={})
            self.db.add(environment)
            self.db.flush()
            self.db.add(ExecutionJob(deployment_plan_id=plan.id, environment_id=environment.id, state="QUEUED", result={"operation": "DEPLOY"}))
            self.audit(principal, "execution.queued", "environment", environment.id, {"plan_hash": plan.plan_hash})
            environments.append(environment)
        self.db.commit()
        return environments

    def run_next_job(self) -> bool:
        """Run one durable fixture job. This is called only by the trusted local worker."""
        job = self.db.scalar(select(ExecutionJob).where(ExecutionJob.state == "QUEUED").order_by(ExecutionJob.created_at).limit(1))
        if not job:
            return False
        environment = self.db.get(Environment, job.environment_id)
        plan = self.db.get(DeploymentPlan, job.deployment_plan_id)
        if not environment or not plan:
            job.state = "FAILED"
            job.result = {"reason": "missing durable plan or environment"}
            self.db.commit()
            return True
        with self._trace("agentconstruct.execution.run"):
            job.state = "RUNNING"
            if plan.action == PlanAction.DESTROY:
                environment.state = LifecycleState.DESTROYING
                observation = self.executor.destroy(environment.id)
                environment.state = LifecycleState.DESTROYED if observation.state == "DESTROYED" else LifecycleState.FAILED
                action = "environment.destroyed" if environment.state == LifecycleState.DESTROYED else "environment.destroy_failed"
            else:
                for state in (LifecycleState.PROVISIONING, LifecycleState.DEPLOYING, LifecycleState.VERIFYING):
                    require_transition(LifecycleState(environment.state), state)
                    environment.state = state
                observation = self.executor.deploy(environment.id, should_fail=bool(environment.desired_state.get("should_fail")))
                environment.state = LifecycleState.READY if observation.state == "READY" else LifecycleState.FAILED
                action = "environment.observed"
            environment.observed_state = observation.detail
            job.state = "SUCCEEDED" if observation.state in {"READY", "DESTROYED"} else "FAILED"
            job.result = {"observation": observation.detail, "state": environment.state}
            principal = Principal(subject="system-worker", organization_id=environment.organization_id, role="operator")
            self.audit(principal, action, "environment", environment.id, {"state": environment.state, "observation": observation.detail})
            self.db.commit()
        return True

    def destroy_plan(self, principal: Principal, environment_id: str) -> DeploymentPlan:
        with self._trace("agentconstruct.destroy.plan"):
            return self._destroy_plan(principal, environment_id)

    def _destroy_plan(self, principal: Principal, environment_id: str) -> DeploymentPlan:
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

    def _queue_destroy(self, principal: Principal, plan: DeploymentPlan) -> Environment:
        if plan.state not in {LifecycleState.PLANNED, LifecycleState.APPROVED}:
            raise ValueError("destroy plan is not executable")
        environment = self._environment(principal, plan.environment_id)
        self.db.add(ExecutionJob(deployment_plan_id=plan.id, environment_id=environment.id, state="QUEUED", result={"operation": "DESTROY"}))
        self.audit(principal, "execution.queued", "environment", environment.id, {"plan_hash": plan.plan_hash})
        self.db.commit()
        return environment


    def _environment(self, principal: Principal, environment_id: str) -> Environment:
        environment = self.db.get(Environment, environment_id)
        if not environment or environment.organization_id != principal.organization_id:
            raise PermissionError("environment not found in this organization")
        return environment

    def audits(self, principal: Principal) -> list[AuditEvent]:
        return list(self.db.scalars(select(AuditEvent).where(AuditEvent.organization_id == principal.organization_id).order_by(AuditEvent.created_at)))
