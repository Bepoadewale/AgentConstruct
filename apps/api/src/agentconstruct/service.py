from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

from httpx import HTTPError
from opentelemetry import trace
from sqlalchemy import select
from sqlalchemy.orm import Session

from agentconstruct.connection_secrets import (
    ConnectionSecretStore,
    configured_connection_secret_store,
)
from agentconstruct.day2 import FixtureDay2Advisor
from agentconstruct.domain import (
    EnvironmentName,
    InfrastructurePlanDecision,
    InfrastructurePlanState,
    LifecycleState,
    PlanAction,
    PolicyResult,
    WorkloadSpec,
)
from agentconstruct.execution_profiles import execution_profile
from agentconstruct.executor import FixtureExecutor
from agentconstruct.integrations import (
    FixtureAwsDiscovery,
    StsAwsDiscovery,
    configured_github_connection,
    verify_github_webhook_signature,
)
from agentconstruct.intent import DeterministicIntentProvider, IntentProvider
from agentconstruct.models import (
    Approval,
    AuditEvent,
    CloudConnection,
    CloudDiscoveryJob,
    CloudReadinessPreflight,
    DeploymentPlan,
    DesiredStatePublication,
    Environment,
    EnvironmentOutput,
    ExecutionJob,
    GitHubAppInstallationState,
    GitHubWebhookDelivery,
    Incident,
    InfrastructurePlan,
    InfrastructurePlanDecisionRecord,
    InfrastructurePlanRevision,
    ObservedResource,
    Organization,
    ProductUser,
    Project,
    Recommendation,
    RepositoryConnection,
    StoredArchitecturePlan,
    StoredCloudInventorySnapshot,
    StoredRepositoryAnalysis,
    TerraformPlanRender,
    TerraformPlanReview,
    WorkloadIntent,
)
from agentconstruct.planner import AwsV1Planner
from agentconstruct.policy import PolicyClient
from agentconstruct.security import Principal
from agentconstruct.state import require_transition


def plan_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class ProductService:
    def __init__(
        self,
        db: Session,
        policy: PolicyClient | None = None,
        executor: FixtureExecutor | None = None,
        intent_provider: IntentProvider | None = None,
        connection_secrets: ConnectionSecretStore | None = None,
    ):
        self.db = db
        self.intent_provider = intent_provider or DeterministicIntentProvider()
        self.planner = AwsV1Planner()
        self.cloud_discovery = FixtureAwsDiscovery()
        self.github = configured_github_connection()
        self.day2_advisor = FixtureDay2Advisor()
        self.policy = policy or PolicyClient()
        self.executor = executor or FixtureExecutor()
        self.connection_secrets = connection_secrets or configured_connection_secret_store()

    def _trace(self, name: str):
        return trace.get_tracer("agentconstruct.product").start_as_current_span(name)

    def seed_local_identity(self) -> None:
        for org_id, name in (("org-demo", "Demo AI Startup"), ("org-other", "Other Tenant")):
            if not self.db.get(Organization, org_id):
                self.db.add(Organization(id=org_id, name=name))
        users = [
            ("user-founder", "org-demo", "developer"),
            ("user-administrator", "org-demo", "administrator"),
            ("user-operator", "org-demo", "operator"),
            ("user-other", "org-other", "developer"),
        ]
        for subject, org_id, role in users:
            if not self.db.scalar(select(ProductUser).where(ProductUser.subject == subject)):
                self.db.add(
                    ProductUser(id=subject, organization_id=org_id, subject=subject, role=role)
                )
        self.db.commit()

    def audit(
        self, principal: Principal, action: str, entity_type: str, entity_id: str, detail: dict
    ) -> None:
        self.db.add(
            AuditEvent(
                organization_id=principal.organization_id,
                actor_subject=principal.subject,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                detail=detail,
            )
        )

    def workspace_profile(self, principal: Principal) -> dict[str, Any]:
        """Return only the current tenant's local identity and workspace metadata."""
        user = self.db.scalar(
            select(ProductUser).where(
                ProductUser.subject == principal.subject,
                ProductUser.organization_id == principal.organization_id,
            )
        )
        organization = self.db.get(Organization, principal.organization_id)
        if not user or not organization:
            raise PermissionError("current user is not a member of this workspace")
        role = "administrator" if self._is_workspace_administrator(principal) else "developer"
        return {
            "user": {"id": user.id, "subject": user.subject, "role": role},
            "workspace": {"id": organization.id, "name": organization.name},
        }

    def workspace_dashboard(self, principal: Principal) -> dict[str, Any]:
        """Tenant-scoped dashboard data. Developers see their plans; admins see workspace plans."""
        profile = self.workspace_profile(principal)
        is_admin = self._is_workspace_administrator(principal)
        projects = self.db.scalars(
            select(Project)
            .where(Project.organization_id == principal.organization_id)
            .order_by(Project.created_at.desc())
        ).all()
        connections = self.db.scalars(
            select(CloudConnection)
            .where(CloudConnection.organization_id == principal.organization_id)
            .order_by(CloudConnection.created_at.desc())
        ).all()
        revisions_query = (
            select(InfrastructurePlanRevision, InfrastructurePlan)
            .join(InfrastructurePlan, InfrastructurePlan.id == InfrastructurePlanRevision.infrastructure_plan_id)
            .where(InfrastructurePlanRevision.organization_id == principal.organization_id)
            .order_by(InfrastructurePlanRevision.created_at.desc())
        )
        if not is_admin:
            revisions_query = revisions_query.where(
                InfrastructurePlan.creator_subject == principal.subject
            )
        revisions = self.db.execute(revisions_query.limit(20)).all()
        activities = self.db.scalars(
            select(AuditEvent)
            .where(AuditEvent.organization_id == principal.organization_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(12)
        ).all()
        pending_count = 0
        if is_admin:
            pending_count = len(
                self.db.scalars(
                    select(InfrastructurePlanRevision.id).where(
                        InfrastructurePlanRevision.organization_id == principal.organization_id,
                        InfrastructurePlanRevision.state == InfrastructurePlanState.SUBMITTED,
                    )
                ).all()
            )
        return {
            **profile,
            "projects": [
                {"id": project.id, "name": project.name, "repository_url": project.repository_url}
                for project in projects
            ],
            "cloud_connections": [
                {
                    "id": connection.id,
                    "display_name": connection.display_name,
                    "provider": connection.provider,
                    "account_id": connection.account_id,
                    "setup_state": connection.setup_state,
                }
                for connection in connections
            ],
            "plans": [
                {
                    "id": revision.id,
                    "plan_id": plan.id,
                    "title": plan.title,
                    "revision": revision.revision_number,
                    "state": revision.state,
                    "creator_subject": plan.creator_subject,
                    "created_at": revision.created_at.isoformat() if revision.created_at else None,
                }
                for revision, plan in revisions
            ],
            "pending_approval_count": pending_count,
            "recent_activity": [
                {
                    "id": event.id,
                    "action": event.action,
                    "entity_type": event.entity_type,
                    "entity_id": event.entity_id,
                    "at": event.created_at.isoformat() if event.created_at else None,
                }
                for event in activities
            ],
        }

    def pending_infrastructure_plan_revisions(self, principal: Principal) -> list[dict[str, Any]]:
        if not self._is_workspace_administrator(principal):
            raise PermissionError("workspace administrator role required for pending approvals")
        rows = self._admin_infrastructure_revision_rows(
            principal, InfrastructurePlanState.SUBMITTED
        )
        return [
            self._admin_plan_queue_item(revision, plan)
            for revision, plan in rows
        ]

    def admin_infrastructure_plan_revisions(
        self, principal: Principal, state: str | None = None
    ) -> list[dict[str, Any]]:
        if not self._is_workspace_administrator(principal):
            raise PermissionError("workspace administrator role required for plan review")
        normalized: InfrastructurePlanState | None = None
        self_approved_only = False
        if state:
            state_key = state.upper()
            if state_key == "SELF_APPROVED":
                normalized = InfrastructurePlanState.APPROVED
                self_approved_only = True
            else:
                normalized = InfrastructurePlanState(state_key)
        rows = self._admin_infrastructure_revision_rows(principal, normalized)
        items = [self._admin_plan_queue_item(revision, plan) for revision, plan in rows]
        if self_approved_only:
            return [item for item in items if item["is_self_approval"]]
        return items

    def _admin_infrastructure_revision_rows(
        self, principal: Principal, state: InfrastructurePlanState | None
    ) -> list[tuple[InfrastructurePlanRevision, InfrastructurePlan]]:
        statement = (
            select(InfrastructurePlanRevision, InfrastructurePlan)
            .join(InfrastructurePlan, InfrastructurePlan.id == InfrastructurePlanRevision.infrastructure_plan_id)
            .where(InfrastructurePlanRevision.organization_id == principal.organization_id)
            .order_by(InfrastructurePlanRevision.created_at.desc())
        )
        if state:
            statement = statement.where(InfrastructurePlanRevision.state == state)
        return list(self.db.execute(statement).all())

    def _admin_plan_queue_item(
        self, revision: InfrastructurePlanRevision, plan: InfrastructurePlan
    ) -> dict[str, Any]:
        decision = self.db.scalar(
            select(InfrastructurePlanDecisionRecord).where(
                InfrastructurePlanDecisionRecord.revision_id == revision.id
            )
        )
        content = revision.content or {}
        target = content.get("target") or {}
        application = content.get("application_analysis") or {}
        policy = content.get("policy_findings") or {}
        return {
            "id": revision.id,
            "plan_id": plan.id,
            "title": plan.title,
            "revision": revision.revision_number,
            "state": revision.state,
            "creator_subject": plan.creator_subject,
            "repository": application.get("repository"),
            "branch": application.get("branch"),
            "aws_account_id": target.get("account_id"),
            "region": target.get("region"),
            "content_digest": revision.content_digest,
            "policy_result": policy.get("result"),
            "is_self_approval": bool(decision and decision.is_self_approval),
            "decision": decision.decision if decision else None,
            "submitted_at": revision.submitted_at.isoformat() if revision.submitted_at else None,
            "decided_at": decision.decided_at.isoformat() if decision and decision.decided_at else None,
            "not_deployed": True,
        }

    def create_project(
        self,
        principal: Principal,
        name: str,
        repository_url: str | None,
        repository_branch: str | None = None,
    ) -> Project:
        project = Project(
            organization_id=principal.organization_id, name=name, repository_url=repository_url
        )
        self.db.add(project)
        self.db.flush()
        if repository_url:
            self.db.add(
                RepositoryConnection(
                    organization_id=principal.organization_id,
                    project_id=project.id,
                    provider="github",
                    repository_url=repository_url,
                    selected_branch=repository_branch,
                )
            )
        self.audit(principal, "project.created", "project", project.id, {"name": name})
        self.db.commit()
        return project

    @staticmethod
    def _is_workspace_administrator(principal: Principal) -> bool:
        # "operator" is the current local fixture name. "administrator" is the product role.
        return principal.role in {"operator", "administrator"}

    def create_infrastructure_plan(
        self,
        principal: Principal,
        project_id: str,
        title: str,
        content: dict[str, Any],
    ) -> InfrastructurePlanRevision:
        """Create a customer-facing DRAFT. It cannot deploy infrastructure."""
        project = self._project(principal, project_id)
        plan = InfrastructurePlan(
            organization_id=principal.organization_id,
            project_id=project.id,
            creator_subject=principal.subject,
            title=title,
        )
        self.db.add(plan)
        self.db.flush()
        revision = self._new_infrastructure_plan_revision(plan, principal, content, 1)
        self.audit(
            principal,
            "infrastructure_plan.draft_created",
            "infrastructure_plan_revision",
            revision.id,
            {"plan_id": plan.id, "revision": revision.revision_number, "digest": revision.content_digest},
        )
        self.db.commit()
        return revision

    def revise_infrastructure_plan(
        self, principal: Principal, plan_id: str, content: dict[str, Any]
    ) -> InfrastructurePlanRevision:
        plan = self._infrastructure_plan(principal, plan_id)
        if plan.creator_subject != principal.subject:
            raise PermissionError("only the plan creator can create a revised draft")
        previous = self.db.scalar(
            select(InfrastructurePlanRevision)
            .where(InfrastructurePlanRevision.infrastructure_plan_id == plan.id)
            .order_by(InfrastructurePlanRevision.revision_number.desc())
            .limit(1)
        )
        if not previous or previous.state not in {
            InfrastructurePlanState.DRAFT,
            InfrastructurePlanState.REJECTED,
        }:
            raise ValueError("a revision can be created only from a draft or rejected plan")
        revision = self._new_infrastructure_plan_revision(
            plan, principal, content, previous.revision_number + 1
        )
        self.audit(
            principal,
            "infrastructure_plan.revised",
            "infrastructure_plan_revision",
            revision.id,
            {"plan_id": plan.id, "revision": revision.revision_number, "digest": revision.content_digest},
        )
        self.db.commit()
        return revision

    def revise_infrastructure_plan_constraints(
        self,
        principal: Principal,
        plan_id: str,
        constraints: dict[str, Any],
    ) -> InfrastructurePlanRevision:
        plan = self._infrastructure_plan(principal, plan_id)
        if plan.creator_subject != principal.subject:
            raise PermissionError("only the plan creator can create a revised draft")
        previous = self.db.scalar(
            select(InfrastructurePlanRevision)
            .where(InfrastructurePlanRevision.infrastructure_plan_id == plan.id)
            .order_by(InfrastructurePlanRevision.revision_number.desc())
            .limit(1)
        )
        if not previous:
            raise ValueError("plan has no revision to update")
        if previous.state not in {
            InfrastructurePlanState.DRAFT,
            InfrastructurePlanState.REJECTED,
        }:
            raise ValueError("a revision can be created only from a draft or rejected plan")
        updated = self._content_with_constraint_updates(previous.content, constraints)
        revision = self.revise_infrastructure_plan(principal, plan_id, updated)
        self.audit(
            principal,
            "infrastructure_plan.constraints_updated",
            "infrastructure_plan_revision",
            revision.id,
            {
                "plan_id": plan.id,
                "revision": revision.revision_number,
                "changed": sorted(
                    key
                    for key, value in constraints.items()
                    if value not in (None, [], {})
                ),
            },
        )
        self.db.commit()
        return revision

    @staticmethod
    def _content_with_constraint_updates(
        content: dict[str, Any], constraints: dict[str, Any]
    ) -> dict[str, Any]:
        updated = json.loads(json.dumps(content))
        workload = updated.setdefault("application_analysis", {}).setdefault(
            "workload_spec", {}
        )
        target = updated.setdefault("target", {})
        summary = updated.setdefault("summary", {})
        previous_constraints = updated.get("user_constraints", {})
        next_constraints = {**previous_constraints}

        if constraints.get("monthly_budget_usd") is not None:
            workload["monthly_budget_usd"] = constraints["monthly_budget_usd"]
            next_constraints["monthly_budget_usd"] = constraints["monthly_budget_usd"]
        if constraints.get("region"):
            workload["region_constraints"] = [constraints["region"]]
            target["region"] = constraints["region"]
            next_constraints["region"] = constraints["region"]
        if constraints.get("environment"):
            environments = [str(item) for item in constraints["environment"]]
            workload["environments"] = environments
            next_constraints["environment"] = environments
        if constraints.get("data_classification"):
            workload["data_classification"] = constraints["data_classification"]
            next_constraints["data_classification"] = constraints["data_classification"]
        if constraints.get("availability_target"):
            workload["availability_target"] = constraints["availability_target"]
            next_constraints["availability_target"] = constraints["availability_target"]
        if constraints.get("workload_type"):
            workload["workload_type"] = constraints["workload_type"]
            next_constraints["workload_type"] = constraints["workload_type"]
        if constraints.get("public_access") is not None:
            workload["requires_private_connectivity"] = not bool(constraints["public_access"])
            next_constraints["public_access"] = bool(constraints["public_access"])

        accepted = constraints.get("accepted_assumptions") or []
        rejected = constraints.get("rejected_assumptions") or []
        updated["assumption_decisions"] = {
            "accepted": accepted,
            "rejected": rejected,
            "note": "Assumption decisions are review inputs; they do not bypass policy or cloud permissions.",
        }
        updated["user_constraints"] = next_constraints
        updated["revision_diff"] = ProductService._revision_diff(content, updated)
        summary["status"] = "DRAFT - revised constraints; not submitted, approved, or deployed"
        return updated

    @staticmethod
    def _revision_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
        before_spec = before.get("application_analysis", {}).get("workload_spec", {})
        after_spec = after.get("application_analysis", {}).get("workload_spec", {})
        before_target = before.get("target", {})
        after_target = after.get("target", {})
        fields = {
            "monthly_budget_usd": (before_spec.get("monthly_budget_usd"), after_spec.get("monthly_budget_usd")),
            "region": (before_target.get("region"), after_target.get("region")),
            "environments": (before_spec.get("environments"), after_spec.get("environments")),
            "data_classification": (before_spec.get("data_classification"), after_spec.get("data_classification")),
            "availability_target": (before_spec.get("availability_target"), after_spec.get("availability_target")),
            "workload_type": (before_spec.get("workload_type"), after_spec.get("workload_type")),
            "requires_private_connectivity": (
                before_spec.get("requires_private_connectivity"),
                after_spec.get("requires_private_connectivity"),
            ),
        }
        return {
            field: {"before": old, "after": new}
            for field, (old, new) in fields.items()
            if old != new
        }

    def _new_infrastructure_plan_revision(
        self,
        plan: InfrastructurePlan,
        principal: Principal,
        content: dict[str, Any],
        revision_number: int,
    ) -> InfrastructurePlanRevision:
        revision = InfrastructurePlanRevision(
            infrastructure_plan_id=plan.id,
            organization_id=principal.organization_id,
            revision_number=revision_number,
            state=InfrastructurePlanState.DRAFT,
            content=content,
            content_digest=plan_hash(content),
        )
        self.db.add(revision)
        self.db.flush()
        return revision

    def submit_infrastructure_plan(
        self, principal: Principal, revision_id: str
    ) -> InfrastructurePlanRevision:
        revision = self._locked_infrastructure_revision(principal, revision_id)
        plan = self._infrastructure_plan(principal, revision.infrastructure_plan_id)
        if plan.creator_subject != principal.subject:
            raise PermissionError("only the plan creator can submit a draft")
        if revision.state != InfrastructurePlanState.DRAFT:
            raise ValueError("only a draft revision can be submitted")
        if revision.content_digest != plan_hash(revision.content):
            raise ValueError("draft content integrity check failed")
        self._validate_infrastructure_plan_submission(principal, plan, revision)
        revision.state = InfrastructurePlanState.SUBMITTED
        revision.submitted_by_subject = principal.subject
        revision.submitted_at = datetime.now(UTC)
        self.audit(
            principal,
            "infrastructure_plan.submitted",
            "infrastructure_plan_revision",
            revision.id,
            {"plan_id": plan.id, "revision": revision.revision_number, "digest": revision.content_digest},
        )
        self.db.commit()
        return revision

    def _validate_infrastructure_plan_submission(
        self,
        principal: Principal,
        plan: InfrastructurePlan,
        revision: InfrastructurePlanRevision,
    ) -> None:
        """Validate the review contract before it becomes an immutable submission.

        This is deliberately a planning gate, not an AWS preflight or deployment action.
        A local fixture target remains valid; selected real connections/repositories must
        still belong to the same workspace.
        """
        content = revision.content
        if content.get("kind") != "agentconstruct.aws.infrastructure-plan.review.v1":
            raise ValueError("only a complete AWS customer-plan review can be submitted")
        target = content.get("target") or {}
        if target.get("provider") != "aws" or not target.get("region"):
            raise ValueError("submitted plan needs an AWS target and region")
        application = content.get("application_analysis") or {}
        if not application.get("repository"):
            raise ValueError("submitted plan needs a selected repository")
        observability = content.get("observability") or {}
        if not observability.get("metrics_backend") or not observability.get("dashboard"):
            raise ValueError("submitted plan needs Prometheus-compatible metrics and Grafana")
        policy = content.get("policy_findings") or {}
        if policy.get("result") == PolicyResult.DENY:
            raise ValueError("policy denied this infrastructure plan")
        connection_id = target.get("connection_id")
        if connection_id:
            self._cloud_connection(principal, str(connection_id))
        # Generated customer reviews carry their source deployment-plan ID. Those
        # reviews must still point at a live project repository before submission.
        # The lower-level lifecycle API remains usable for independently created
        # typed plan fixtures and migration data.
        if content.get("source_deployment_plan_id"):
            repository = self.db.scalar(
                select(RepositoryConnection).where(
                    RepositoryConnection.organization_id == principal.organization_id,
                    RepositoryConnection.project_id == plan.project_id,
                    RepositoryConnection.repository_url == application["repository"],
                )
            )
            if repository is None:
                raise ValueError("selected repository is no longer connected to this project")

    def infrastructure_plan_revision_detail(
        self, principal: Principal, revision_id: str
    ) -> dict[str, Any]:
        revision = self._infrastructure_revision(principal, revision_id)
        plan = self._infrastructure_plan(principal, revision.infrastructure_plan_id)
        if not self._is_workspace_administrator(principal) and plan.creator_subject != principal.subject:
            raise PermissionError("infrastructure plan revision is not visible to this user")
        decision = self.db.scalar(
            select(InfrastructurePlanDecisionRecord).where(
                InfrastructurePlanDecisionRecord.revision_id == revision.id
            )
        )
        content = revision.content or {}
        application = content.get("application_analysis") or {}
        target = content.get("target") or {}
        observability = content.get("observability") or {}
        cost = content.get("cost_estimate") or {}
        policy = content.get("policy_findings") or {}
        risks = content.get("risks_and_limitations") or []
        local_executions = self._customer_plan_environment_summaries(principal, revision.id)
        desired_state_publications = [
            self._desired_state_publication_payload(publication)
            for publication in self.db.scalars(
                select(DesiredStatePublication)
                .where(
                    DesiredStatePublication.organization_id == principal.organization_id,
                    DesiredStatePublication.revision_id == revision.id,
                )
                .order_by(DesiredStatePublication.created_at.desc())
            )
        ]
        terraform_plan_renders = [
            self._terraform_plan_render_payload(render)
            for render in self.db.scalars(
                select(TerraformPlanRender)
                .where(
                    TerraformPlanRender.organization_id == principal.organization_id,
                    TerraformPlanRender.revision_id == revision.id,
                )
                .order_by(TerraformPlanRender.created_at.desc())
            )
        ]
        cloud_preflights = [
            self._cloud_readiness_preflight_payload(preflight)
            for preflight in self.db.scalars(
                select(CloudReadinessPreflight)
                .where(
                    CloudReadinessPreflight.organization_id == principal.organization_id,
                    CloudReadinessPreflight.revision_id == revision.id,
                )
                .order_by(CloudReadinessPreflight.created_at.desc())
            )
        ]
        terraform_plan_reviews = [
            self._terraform_plan_review_payload(review)
            for review in self.db.scalars(
                select(TerraformPlanReview)
                .where(
                    TerraformPlanReview.organization_id == principal.organization_id,
                    TerraformPlanReview.revision_id == revision.id,
                )
                .order_by(TerraformPlanReview.created_at.desc())
            )
        ]
        return {
            "id": revision.id,
            "plan_id": plan.id,
            "title": plan.title,
            "creator_subject": plan.creator_subject,
            "revision": revision.revision_number,
            "state": revision.state,
            "content_digest": revision.content_digest,
            "content": content,
            "review_summary": {
                "requester": plan.creator_subject,
                "repository": application.get("repository"),
                "branch": application.get("branch"),
                "aws_account_id": target.get("account_id"),
                "region": target.get("region"),
                "policy_result": policy.get("result"),
                "prometheus": observability.get("metrics_backend"),
                "grafana": observability.get("dashboard"),
                "estimated_cost": cost.get("range"),
                "risks": risks,
                "approved_not_deployed": revision.state == InfrastructurePlanState.APPROVED,
                "execution_boundary": "Approval records a decision only. It does not deploy or mutate AWS resources.",
            },
            "local_executions": local_executions,
            "desired_state_publications": desired_state_publications,
            "terraform_plan_renders": terraform_plan_renders,
            "cloud_readiness_preflights": cloud_preflights,
            "terraform_plan_reviews": terraform_plan_reviews,
            "submitted_by_subject": revision.submitted_by_subject,
            "submitted_at": revision.submitted_at.isoformat() if revision.submitted_at else None,
            "decision": None
            if not decision
            else {
                "decision": decision.decision,
                "approver_subject": decision.approver_subject,
                "creator_subject": decision.creator_subject,
                "is_self_approval": decision.is_self_approval,
                "approved_digest": decision.approved_digest,
                "authorization_policy": decision.authorization_policy,
                "reason": decision.reason,
                "decided_at": decision.decided_at.isoformat() if decision.decided_at else None,
            },
            "execution": "UNEXECUTED_APPROVAL_ONLY",
        }

    def execute_customer_plan_dry_run(
        self, principal: Principal, revision_id: str
    ) -> list[Environment]:
        """Queue a bounded local fixture run for an approved customer-plan revision.

        This is deliberately separate from approval and never assumes AWS credentials.
        """
        revision, plan, source_deployment = self._approved_customer_revision(principal, revision_id)
        if not self._is_workspace_administrator(principal) and plan.creator_subject != principal.subject:
            raise PermissionError("only the plan creator or a workspace administrator can execute the local dry run")
        existing = self._customer_plan_environments(principal, revision.id)
        active = [
            environment
            for environment in existing
            if LifecycleState(environment.state) != LifecycleState.DESTROYED
        ]
        if active:
            return active
        payload = {
            **source_deployment.payload,
            "execution_mode": "LOCAL_DRY_RUN",
            "customer_plan_revision_id": revision.id,
            "customer_plan_digest": revision.content_digest,
            "customer_plan_approved": True,
            "execution_boundary": "bounded local fixture execution only; no AWS resources are created",
        }
        digest = plan_hash(
            {
                "action": PlanAction.DEPLOY,
                "execution_mode": "LOCAL_DRY_RUN",
                "revision_id": revision.id,
                "digest": revision.content_digest,
                "payload": payload,
            }
        )
        dry_run = self.db.scalar(select(DeploymentPlan).where(DeploymentPlan.plan_hash == digest))
        if not dry_run:
            dry_run = DeploymentPlan(
                organization_id=principal.organization_id,
                intent_id=source_deployment.intent_id,
                requester_subject=principal.subject,
                action=PlanAction.DEPLOY,
                state=LifecycleState.PLANNED,
                plan_hash=digest,
                policy_result=PolicyResult.ALLOW,
                payload=payload,
            )
            self.db.add(dry_run)
            self.db.flush()
            self.audit(
                principal,
                "customer_plan.local_dry_run_plan_created",
                "deployment_plan",
                dry_run.id,
                {"revision_id": revision.id, "digest": revision.content_digest},
            )
        environments = self.execute(principal, dry_run.id)
        self.audit(
            principal,
            "customer_plan.local_dry_run_queued",
            "infrastructure_plan_revision",
            revision.id,
            {
                "deployment_plan_id": dry_run.id,
                "environment_ids": [environment.id for environment in environments],
                "digest": revision.content_digest,
            },
        )
        self.db.commit()
        return environments

    def customer_plan_destroy_plan(
        self, principal: Principal, revision_id: str, environment_id: str
    ) -> DeploymentPlan:
        revision, _, _ = self._approved_customer_revision(principal, revision_id)
        environment = self._environment(principal, environment_id)
        if environment.desired_state.get("customer_plan_revision_id") != revision.id:
            raise PermissionError("environment is not tied to this customer-plan revision")
        if LifecycleState(environment.state) not in {
            LifecycleState.READY,
            LifecycleState.FAILED,
            LifecycleState.DEGRADED,
        }:
            raise ValueError("environment cannot be destroyed in its current state")
        environment.state = LifecycleState.DESTROY_REQUESTED
        requires_approval = environment.environment_type == EnvironmentName.PRODUCTION
        payload = {
            "action": PlanAction.DESTROY,
            "environment_id": environment.id,
            "observed_state": environment.observed_state,
            "customer_plan_revision_id": revision.id,
            "customer_plan_digest": revision.content_digest,
            "execution_mode": "LOCAL_DRY_RUN_DESTROY",
        }
        digest = plan_hash(payload)
        plan = DeploymentPlan(
            organization_id=principal.organization_id,
            environment_id=environment.id,
            requester_subject=principal.subject,
            action=PlanAction.DESTROY,
            state=LifecycleState.DESTROY_APPROVAL_REQUIRED
            if requires_approval
            else LifecycleState.PLANNED,
            plan_hash=digest,
            policy_result=PolicyResult.APPROVAL_REQUIRED
            if requires_approval
            else PolicyResult.ALLOW,
            payload=payload,
        )
        self.db.add(plan)
        self.db.flush()
        self.audit(
            principal,
            "customer_plan.local_destroy_requested",
            "infrastructure_plan_revision",
            revision.id,
            {
                "environment_id": environment.id,
                "deployment_plan_id": plan.id,
                "hash": digest,
                "approval_required": requires_approval,
            },
        )
        self.db.commit()
        return plan

    def _approved_customer_revision(
        self, principal: Principal, revision_id: str
    ) -> tuple[InfrastructurePlanRevision, InfrastructurePlan, DeploymentPlan]:
        revision = self._infrastructure_revision(principal, revision_id)
        plan = self._infrastructure_plan(principal, revision.infrastructure_plan_id)
        if not self._is_workspace_administrator(principal) and plan.creator_subject != principal.subject:
            raise PermissionError("infrastructure plan revision is not visible to this user")
        if revision.state != InfrastructurePlanState.APPROVED:
            raise ValueError("customer-plan revision must be approved before local dry-run execution")
        decision = self.db.scalar(
            select(InfrastructurePlanDecisionRecord).where(
                InfrastructurePlanDecisionRecord.revision_id == revision.id
            )
        )
        if not decision or decision.decision != InfrastructurePlanDecision.APPROVED:
            raise ValueError("approved customer-plan revision has no durable approval decision")
        if decision.approved_digest != revision.content_digest:
            raise ValueError("approved customer-plan digest no longer matches the revision")
        source_id = revision.content.get("source_deployment_plan_id")
        if not source_id:
            raise ValueError("customer-plan revision has no source execution contract")
        source = self._plan(principal, str(source_id))
        return revision, plan, source

    def _customer_plan_environments(
        self, principal: Principal, revision_id: str
    ) -> list[Environment]:
        return [
            environment
            for environment in self.db.scalars(
                select(Environment)
                .where(Environment.organization_id == principal.organization_id)
                .order_by(Environment.created_at)
            )
            if environment.desired_state.get("customer_plan_revision_id") == revision_id
        ]

    def _customer_plan_environment_summaries(
        self, principal: Principal, revision_id: str
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": environment.id,
                "name": environment.name,
                "type": environment.environment_type,
                "state": environment.state,
                "execution_mode": environment.desired_state.get("execution_mode"),
                "plan_hash": environment.desired_state.get("plan_hash"),
                "cost_estimate": environment.desired_state.get("cost_estimate"),
                "observed_state": environment.observed_state,
                "outputs": self._environment_outputs(environment.id),
                "resources": self._observed_resources(environment.id),
            }
            for environment in self._customer_plan_environments(principal, revision_id)
        ]

    def _record_environment_observation_assets(
        self, environment: Environment, observation: dict[str, Any]
    ) -> None:
        forced_status = "DESTROYED" if observation.get("state") == "DESTROYED" else None
        for item in observation.get("outputs", []):
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            output = self.db.scalar(
                select(EnvironmentOutput).where(
                    EnvironmentOutput.environment_id == environment.id,
                    EnvironmentOutput.name == name,
                )
            )
            if not output:
                output = EnvironmentOutput(
                    organization_id=environment.organization_id,
                    environment_id=environment.id,
                    name=name,
                    output_type=str(item.get("type") or "value"),
                    value=str(item.get("value") or ""),
                )
                self.db.add(output)
            output.output_type = str(item.get("type") or output.output_type)
            output.value = str(item.get("value") or output.value)
            output.visibility = str(item.get("visibility") or "customer")
            output.sensitive = str(bool(item.get("sensitive", False))).lower()
            output.source = str(item.get("source") or "fixture-observer")
            output.status = forced_status or str(item.get("status") or output.status)
            output.detail = {
                key: value
                for key, value in item.items()
                if key
                not in {
                    "name",
                    "type",
                    "value",
                    "visibility",
                    "sensitive",
                    "source",
                    "status",
                }
            }

        for item in observation.get("resources", []):
            provider = str(item.get("provider") or "unknown")
            resource_type = str(item.get("resource_type") or item.get("type") or "unknown")
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            resource = self.db.scalar(
                select(ObservedResource).where(
                    ObservedResource.environment_id == environment.id,
                    ObservedResource.provider == provider,
                    ObservedResource.resource_type == resource_type,
                    ObservedResource.name == name,
                )
            )
            if not resource:
                resource = ObservedResource(
                    organization_id=environment.organization_id,
                    environment_id=environment.id,
                    provider=provider,
                    resource_type=resource_type,
                    name=name,
                )
                self.db.add(resource)
            resource.external_id = item.get("external_id")
            resource.region = item.get("region")
            resource.status = forced_status or str(item.get("status") or resource.status)
            resource.tags = dict(item.get("tags") or {})
            resource.detail = {
                key: value
                for key, value in item.items()
                if key
                not in {
                    "provider",
                    "resource_type",
                    "type",
                    "name",
                    "external_id",
                    "region",
                    "status",
                    "tags",
                }
            }

    def _environment_outputs(self, environment_id: str) -> list[dict[str, Any]]:
        return [
            {
                "id": output.id,
                "name": output.name,
                "type": output.output_type,
                "value": "***" if output.sensitive == "true" else output.value,
                "visibility": output.visibility,
                "sensitive": output.sensitive == "true",
                "source": output.source,
                "status": output.status,
                "detail": output.detail,
                "updated_at": output.updated_at.isoformat() if output.updated_at else None,
            }
            for output in self.db.scalars(
                select(EnvironmentOutput)
                .where(EnvironmentOutput.environment_id == environment_id)
                .order_by(EnvironmentOutput.name)
            )
        ]

    def _observed_resources(self, environment_id: str) -> list[dict[str, Any]]:
        return [
            {
                "id": resource.id,
                "provider": resource.provider,
                "type": resource.resource_type,
                "name": resource.name,
                "external_id": resource.external_id,
                "region": resource.region,
                "status": resource.status,
                "tags": resource.tags,
                "detail": resource.detail,
                "updated_at": resource.updated_at.isoformat() if resource.updated_at else None,
            }
            for resource in self.db.scalars(
                select(ObservedResource)
                .where(ObservedResource.environment_id == environment_id)
                .order_by(
                    ObservedResource.provider,
                    ObservedResource.resource_type,
                    ObservedResource.name,
                )
            )
        ]

    def decide_infrastructure_plan(
        self,
        principal: Principal,
        revision_id: str,
        decision: InfrastructurePlanDecision,
        provided_digest: str,
        reason: str | None = None,
    ) -> InfrastructurePlanRevision:
        if not self._is_workspace_administrator(principal):
            raise PermissionError("workspace administrator role required for a plan decision")
        revision = self._locked_infrastructure_revision(principal, revision_id)
        plan = self._infrastructure_plan(principal, revision.infrastructure_plan_id)
        if revision.state != InfrastructurePlanState.SUBMITTED:
            raise ValueError("only a submitted revision can be decided")
        if revision.content_digest != provided_digest or plan_hash(revision.content) != provided_digest:
            raise ValueError("stale decision: submitted plan digest changed")
        if decision == InfrastructurePlanDecision.REJECTED and not (reason or "").strip():
            raise ValueError("a rejection reason is required")
        record = InfrastructurePlanDecisionRecord(
            revision_id=revision.id,
            organization_id=principal.organization_id,
            decision=decision,
            approver_subject=principal.subject,
            creator_subject=plan.creator_subject,
            is_self_approval=decision == InfrastructurePlanDecision.APPROVED
            and principal.subject == plan.creator_subject,
            approved_digest=provided_digest,
            authorization_policy="workspace-administrator-self-approval-allowed"
            if principal.subject == plan.creator_subject
            else "workspace-administrator",
            reason=reason.strip() if reason else None,
        )
        self.db.add(record)
        revision.state = (
            InfrastructurePlanState.APPROVED
            if decision == InfrastructurePlanDecision.APPROVED
            else InfrastructurePlanState.REJECTED
        )
        self.audit(
            principal,
            f"infrastructure_plan.{decision.lower()}",
            "infrastructure_plan_revision",
            revision.id,
            {
                "plan_id": plan.id,
                "revision": revision.revision_number,
                "digest": provided_digest,
                "is_self_approval": record.is_self_approval,
                "authorization_policy": record.authorization_policy,
                "reason": record.reason,
            },
        )
        self.db.commit()
        return revision

    def _infrastructure_plan(self, principal: Principal, plan_id: str) -> InfrastructurePlan:
        plan = self.db.get(InfrastructurePlan, plan_id)
        if not plan or plan.organization_id != principal.organization_id:
            raise PermissionError("infrastructure plan not found in this organization")
        return plan

    def _infrastructure_revision(
        self, principal: Principal, revision_id: str
    ) -> InfrastructurePlanRevision:
        revision = self.db.get(InfrastructurePlanRevision, revision_id)
        if not revision or revision.organization_id != principal.organization_id:
            raise PermissionError("infrastructure plan revision not found in this organization")
        return revision

    def _locked_infrastructure_revision(
        self, principal: Principal, revision_id: str
    ) -> InfrastructurePlanRevision:
        """Use a row lock where supported so concurrent decisions cannot both win."""
        revision = self.db.scalar(
            select(InfrastructurePlanRevision)
            .where(
                InfrastructurePlanRevision.id == revision_id,
                InfrastructurePlanRevision.organization_id == principal.organization_id,
            )
            .with_for_update()
        )
        if not revision:
            raise PermissionError("infrastructure plan revision not found in this organization")
        return revision

    def create_cloud_connection(
        self, principal: Principal, display_name: str, provider: str, connection_mode: str
    ) -> CloudConnection:
        connection = CloudConnection(
            organization_id=principal.organization_id,
            display_name=display_name,
            provider=provider,
            connection_mode=connection_mode,
        )
        self.db.add(connection)
        self.db.flush()
        self.audit(
            principal,
            "cloud_connection.created",
            "cloud_connection",
            connection.id,
            {"provider": provider, "mode": connection_mode},
        )
        self.db.commit()
        return connection

    def cloud_connections(self, principal: Principal) -> list[CloudConnection]:
        return list(
            self.db.scalars(
                select(CloudConnection)
                .where(CloudConnection.organization_id == principal.organization_id)
                .order_by(CloudConnection.created_at)
            )
        )

    def cloud_connection_detail(self, principal: Principal, connection_id: str) -> dict[str, Any]:
        connection = self._cloud_connection(principal, connection_id)
        latest = self.db.scalar(
            select(StoredCloudInventorySnapshot)
            .where(
                StoredCloudInventorySnapshot.organization_id == principal.organization_id,
                StoredCloudInventorySnapshot.cloud_connection_id == connection.id,
            )
            .order_by(StoredCloudInventorySnapshot.captured_at.desc())
            .limit(1)
        )
        snapshot = latest.snapshot if latest else {}
        return {
            "id": connection.id,
            "display_name": connection.display_name,
            "provider": connection.provider,
            "account_id": connection.account_id,
            "role_arn": connection.discovery_role_arn,
            "setup_state": connection.setup_state,
            "authorized_regions": snapshot.get("approved_regions", []),
            "capabilities": [
                "read-only inventory discovery",
                "read-only Cost Explorer query when customer policy permits",
            ],
            "verified_at": latest.captured_at.isoformat() if latest else None,
            "verification_provenance": latest.provenance if latest else None,
            "credentials_stored": False,
            "deployment_permission": "not granted",
        }

    def disconnect_cloud_connection(self, principal: Principal, connection_id: str) -> None:
        connection = self._cloud_connection(principal, connection_id)
        self.db.query(CloudDiscoveryJob).filter(
            CloudDiscoveryJob.cloud_connection_id == connection.id
        ).delete(synchronize_session=False)
        self.db.query(StoredCloudInventorySnapshot).filter(
            StoredCloudInventorySnapshot.cloud_connection_id == connection.id
        ).delete(synchronize_session=False)
        self.db.delete(connection)
        self.audit(
            principal,
            "cloud_connection.disconnected",
            "cloud_connection",
            connection_id,
            {"credentials_stored": False},
        )
        self.db.commit()

    def _cloud_connection(self, principal: Principal, connection_id: str) -> CloudConnection:
        connection = self.db.get(CloudConnection, connection_id)
        if not connection or connection.organization_id != principal.organization_id:
            raise PermissionError("cloud connection not found in this organization")
        return connection

    def aws_quick_create_setup(
        self, principal: Principal, connection_id: str, account_id: str
    ) -> dict[str, object]:
        """Generate a one-click AWS Console setup; it does not create AWS resources itself."""
        connection = self._cloud_connection(principal, connection_id)
        control_plane_role_arn = os.getenv("AGENTCONSTRUCT_CONTROL_PLANE_ROLE_ARN")
        template_url = os.getenv("AGENTCONSTRUCT_AWS_CONNECTION_TEMPLATE_URL")
        if not control_plane_role_arn or not template_url:
            raise RuntimeError("AWS customer connection setup is not configured with a hosted template")
        external_id = secrets.token_urlsafe(32)
        stack_name = f"AgentConstruct-Discovery-{connection.id[:8]}"
        discovery_role_arn = (
            f"arn:aws:iam::{account_id}:role/AgentConstructDiscovery-{connection.id}"
        )
        parameters = {
            "AgentConstructControlPlaneRoleArn": control_plane_role_arn,
            "ExternalId": external_id,
            "ConnectionId": connection.id,
        }
        quick_create_url = (
            "https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?"
            + urlencode({"templateURL": template_url, "stackName": stack_name})
            + "&"
            + urlencode({f"param_{key}": value for key, value in parameters.items()})
        )
        connection.account_id = account_id
        connection.discovery_role_arn = discovery_role_arn
        connection.external_id_secret_ref = self.connection_secrets.put_external_id(
            principal.organization_id, connection.id, external_id
        )
        # Do not retain a plaintext legacy value. Existing values require a new setup link.
        connection.external_id = None
        connection.setup_state = "SETUP_LINK_GENERATED"
        self.audit(
            principal,
            "cloud_connection.aws_quick_create_generated",
            "cloud_connection",
            connection.id,
            {"account_id": account_id, "stack_name": stack_name, "template_published": bool(template_url)},
        )
        self.db.commit()
        return {
            "connection_id": connection.id,
            "account_id": account_id,
            "stack_name": stack_name,
            "template_path": "infrastructure/cloudformation/customer-discovery-role.yaml",
            "quick_create_url": quick_create_url,
            "customer_steps": [
                "Open the AWS Quick Create link.",
                "Review the one read-only IAM role and acknowledge IAM resource creation.",
                "Create the stack, then return to AgentConstruct to verify the connection.",
            ],
            "boundary": "This action only creates a setup link. AgentConstruct does not create customer AWS resources until the customer creates the stack in their own account.",
        }

    def queue_aws_connection_verification(
        self, principal: Principal, connection_id: str, region: str
    ) -> CloudDiscoveryJob:
        connection = self._cloud_connection(principal, connection_id)
        if not all([connection.account_id, connection.discovery_role_arn, connection.external_id_secret_ref]):
            raise ValueError("generate a new AWS setup link before verifying this connection")
        if os.getenv("AGENTCONSTRUCT_AWS_LIVE_DISCOVERY_ENABLED", "false").lower() != "true":
            raise RuntimeError("live AWS discovery is not enabled for this control-plane process")
        job = CloudDiscoveryJob(
            organization_id=principal.organization_id,
            cloud_connection_id=connection.id,
            requester_subject=principal.subject,
            region=region,
            state="QUEUED",
            result={"operation": "READ_ONLY_AWS_DISCOVERY"},
        )
        self.db.add(job)
        self.db.flush()
        self.audit(
            principal,
            "cloud_connection.aws_verification_queued",
            "cloud_discovery_job",
            job.id,
            {"connection_id": connection.id, "region": region},
        )
        self.db.commit()
        return job

    def cloud_discovery_job(
        self, principal: Principal, connection_id: str, job_id: str
    ) -> CloudDiscoveryJob:
        job = self.db.get(CloudDiscoveryJob, job_id)
        if (
            not job
            or job.organization_id != principal.organization_id
            or job.cloud_connection_id != connection_id
        ):
            raise PermissionError("cloud discovery job not found in this organization")
        return job

    def verify_aws_connection(
        self,
        principal: Principal,
        connection_id: str,
        region: str,
        discovery: StsAwsDiscovery | None = None,
    ) -> StoredCloudInventorySnapshot:
        """Assume only the per-customer read-only role and store no credentials."""
        connection = self._cloud_connection(principal, connection_id)
        if not all([connection.account_id, connection.discovery_role_arn, connection.external_id_secret_ref]):
            raise ValueError("generate a new AWS setup link before verifying this connection")
        if os.getenv("AGENTCONSTRUCT_AWS_LIVE_DISCOVERY_ENABLED", "false").lower() != "true":
            raise RuntimeError("live AWS discovery is not enabled for this control-plane process")
        external_id = self.connection_secrets.get_external_id(connection.external_id_secret_ref)
        snapshot = (discovery or StsAwsDiscovery()).verify(
            connection.id, connection.discovery_role_arn, external_id, region
        )
        discovered_account = next(
            (
                item.removeprefix("aws-account:")
                for item in snapshot.approved_resources
                if item.startswith("aws-account:")
            ),
            None,
        )
        if discovered_account != connection.account_id:
            raise PermissionError("assumed AWS role belongs to a different account")
        connection.setup_state = "VERIFIED"
        self.audit(
            principal,
            "cloud_connection.aws_verified",
            "cloud_connection",
            connection.id,
            {"account_id": connection.account_id, "region": region, "provenance": snapshot.provenance},
        )
        self.db.commit()
        return self.record_cloud_inventory_snapshot(
            principal,
            connection.id,
            region,
            snapshot.provenance,
            snapshot.discovered_at,
            snapshot.model_dump(mode="json"),
        )

    def run_next_discovery_job(self) -> bool:
        """Process one durable read-only discovery job; no cloud mutation occurs here."""
        job = self.db.scalar(
            select(CloudDiscoveryJob)
            .where(CloudDiscoveryJob.state == "QUEUED")
            .order_by(CloudDiscoveryJob.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        if not job:
            return False
        job.state = "RUNNING"
        job.attempts += 1
        self.db.commit()
        principal = Principal(job.requester_subject, job.organization_id, "developer")
        try:
            snapshot = self.verify_aws_connection(principal, job.cloud_connection_id, job.region)
            job.state = "SUCCEEDED"
            job.result = {"snapshot_id": snapshot.id, "provenance": snapshot.provenance}
            job.error = None
            self.audit(
                principal,
                "cloud_connection.aws_verification_succeeded",
                "cloud_discovery_job",
                job.id,
                {"connection_id": job.cloud_connection_id, "snapshot_id": snapshot.id},
            )
        except Exception as error:  # noqa: BLE001 - worker records bounded provider failures safely.
            job.state = "FAILED"
            job.error = str(error)[:300]
            job.result = {}
            self.audit(
                principal,
                "cloud_connection.aws_verification_failed",
                "cloud_discovery_job",
                job.id,
                {"connection_id": job.cloud_connection_id, "reason": job.error},
            )
        self.db.commit()
        return True

    def record_cloud_inventory_snapshot(
        self,
        principal: Principal,
        connection_id: str,
        region: str,
        provenance: str,
        captured_at,
        snapshot: dict[str, Any],
    ) -> StoredCloudInventorySnapshot:
        """Persist metadata discovered through STS; credential material is never accepted."""
        connection = self._cloud_connection(principal, connection_id)
        stored = StoredCloudInventorySnapshot(
            organization_id=principal.organization_id,
            cloud_connection_id=connection.id,
            region=region,
            provenance=provenance,
            captured_at=captured_at,
            snapshot=snapshot,
        )
        self.db.add(stored)
        self.db.flush()
        self.audit(
            principal,
            "cloud_inventory.snapshot_recorded",
            "cloud_inventory_snapshot",
            stored.id,
            {"connection_id": connection.id, "region": region, "provenance": provenance},
        )
        self.db.commit()
        return stored

    def cloud_inventory_snapshots(
        self, principal: Principal, connection_id: str
    ) -> list[StoredCloudInventorySnapshot]:
        connection = self.db.get(CloudConnection, connection_id)
        if not connection or connection.organization_id != principal.organization_id:
            raise PermissionError("cloud connection not found in this organization")
        return list(
            self.db.scalars(
                select(StoredCloudInventorySnapshot)
                .where(
                    StoredCloudInventorySnapshot.organization_id == principal.organization_id,
                    StoredCloudInventorySnapshot.cloud_connection_id == connection_id,
                )
                .order_by(StoredCloudInventorySnapshot.captured_at.desc())
            )
        )

    def github_connection_status(self, principal: Principal) -> dict[str, Any]:
        states = list(
            self.db.scalars(
                select(GitHubAppInstallationState)
                .where(GitHubAppInstallationState.organization_id == principal.organization_id)
                .order_by(GitHubAppInstallationState.updated_at.desc())
            )
        )
        recent_deliveries = list(
            self.db.scalars(
                select(GitHubWebhookDelivery)
                .where(GitHubWebhookDelivery.organization_id == principal.organization_id)
                .order_by(GitHubWebhookDelivery.received_at.desc())
                .limit(5)
            )
        )
        execution = getattr(self.github, "execution", "SIMULATED")
        try:
            installations = [item.__dict__ for item in self.github.installations()]
        except HTTPError as error:
            raise ValueError(
                "GitHub App connection is unavailable, expired, or missing permissions"
            ) from error
        return {
            "mode": "read-only",
            "execution": execution,
            "installations": installations,
            "install_url": os.getenv("AGENTCONSTRUCT_GITHUB_APP_INSTALL_URL"),
            "writes_enabled": False,
            "credentials_stored": False,
            "webhooks_enabled": bool(os.getenv("AGENTCONSTRUCT_GITHUB_WEBHOOK_SECRET"))
            or execution == "SIMULATED",
            "installation_states": [
                {
                    "installation_id": item.installation_id,
                    "account_login": item.account_login,
                    "account_type": item.account_type,
                    "state": item.state,
                    "repository_selection": item.repository_selection,
                    "permissions": item.permissions,
                    "last_event": item.last_event,
                    "updated_at": item.updated_at,
                }
                for item in states
            ],
            "recent_webhook_deliveries": [
                {
                    "delivery_id": item.delivery_id,
                    "event": item.event,
                    "action": item.action,
                    "installation_id": item.installation_id,
                    "repository": item.repository,
                    "status": item.status,
                    "received_at": item.received_at,
                }
                for item in recent_deliveries
            ],
        }

    def receive_github_webhook(
        self,
        *,
        event: str,
        delivery_id: str,
        signature: str,
        body: bytes,
    ) -> dict[str, Any]:
        """Process a signed GitHub App webhook without exposing repository credentials.

        In local fixture mode, ``fixture-sha256=valid`` is accepted so tests can
        exercise product state transitions without a public callback URL.
        In configured mode, the standard GitHub HMAC signature is required.
        """
        if not event or not delivery_id:
            raise ValueError("GitHub event and delivery ID are required")
        execution = getattr(self.github, "execution", "SIMULATED")
        secret = os.getenv("AGENTCONSTRUCT_GITHUB_WEBHOOK_SECRET", "")
        fixture_signature = execution == "SIMULATED" and signature == "fixture-sha256=valid"
        if not fixture_signature and not verify_github_webhook_signature(secret, body, signature):
            raise PermissionError("GitHub webhook signature is invalid")
        duplicate = self.db.scalar(
            select(GitHubWebhookDelivery).where(GitHubWebhookDelivery.delivery_id == delivery_id)
        )
        if duplicate:
            return {
                "status": "DUPLICATE",
                "delivery_id": duplicate.delivery_id,
                "event": duplicate.event,
                "installation_id": duplicate.installation_id,
                "state": "UNCHANGED",
            }
        try:
            payload = json.loads(body.decode() or "{}")
        except json.JSONDecodeError as error:
            raise ValueError("GitHub webhook payload must be valid JSON") from error
        organization_id = self._github_webhook_organization_id(payload)
        installation = payload.get("installation") or {}
        account = installation.get("account") or payload.get("sender") or {}
        repository = payload.get("repository") or {}
        installation_id = str(installation.get("id") or "fixture-installation")
        account_login = str(account.get("login") or "unknown-github-account")
        account_type = str(account.get("type") or "Organization")
        action = payload.get("action")
        repository_name = repository.get("full_name")
        state = self._github_installation_state(event, action, payload)
        permissions = installation.get("permissions") or payload.get("permissions") or {}
        repository_selection = str(installation.get("repository_selection") or "selected")
        install_state = self.db.scalar(
            select(GitHubAppInstallationState).where(
                GitHubAppInstallationState.organization_id == organization_id,
                GitHubAppInstallationState.installation_id == installation_id,
            )
        )
        last_event = {
            "event": event,
            "action": action,
            "repository": repository_name,
            "delivery_id": delivery_id,
            "execution": execution,
        }
        if install_state:
            install_state.account_login = account_login
            install_state.account_type = account_type
            install_state.state = state
            install_state.repository_selection = repository_selection
            install_state.permissions = permissions
            install_state.last_event = last_event
        else:
            install_state = GitHubAppInstallationState(
                organization_id=organization_id,
                installation_id=installation_id,
                account_login=account_login,
                account_type=account_type,
                state=state,
                repository_selection=repository_selection,
                permissions=permissions,
                last_event=last_event,
            )
            self.db.add(install_state)
        delivery = GitHubWebhookDelivery(
            organization_id=organization_id,
            delivery_id=delivery_id,
            event=event,
            action=action,
            installation_id=installation_id,
            repository=repository_name,
            status="PROCESSED",
            detail=last_event,
        )
        self.db.add(delivery)
        self.db.flush()
        self.db.add(
            AuditEvent(
                organization_id=organization_id,
                actor_subject="github-app",
                action=f"github.webhook.{event}",
                entity_type="github_app_installation",
                entity_id=install_state.id,
                detail=last_event | {"state": state},
            )
        )
        self.db.commit()
        return {
            "status": "PROCESSED",
            "delivery_id": delivery_id,
            "event": event,
            "action": action,
            "installation_id": installation_id,
            "repository": repository_name,
            "state": state,
            "execution": execution,
        }

    def _github_webhook_organization_id(self, payload: dict[str, Any]) -> str:
        requested = (payload.get("agentconstruct") or {}).get("organization_id")
        organization_id = str(requested or os.getenv("AGENTCONSTRUCT_DEFAULT_WEBHOOK_ORG", "org-demo"))
        if not self.db.get(Organization, organization_id):
            raise PermissionError("GitHub webhook installation is not mapped to a workspace")
        return organization_id

    @staticmethod
    def _github_installation_state(
        event: str, action: str | None, payload: dict[str, Any]
    ) -> str:
        permissions = (
            (payload.get("installation") or {}).get("permissions")
            or payload.get("permissions")
            or {}
        )
        if permissions and permissions.get("metadata") not in {None, "read"}:
            return "MISSING_PERMISSION"
        if event == "installation" and action == "deleted":
            return "REVOKED"
        if event == "installation" and action == "suspend":
            return "SUSPENDED"
        if event == "repository" and action in {"deleted", "transferred"}:
            return "REPOSITORY_INACCESSIBLE"
        if event == "installation_repositories":
            return "REPOSITORY_ACCESS_CHANGED"
        if event == "push":
            return "BRANCH_UPDATED"
        return "CONNECTED"

    def github_repositories(self, principal: Principal, installation_id: str) -> list[dict[str, str]]:
        del principal  # The configured adapter independently scopes access to installation repositories.
        try:
            return [item.__dict__ for item in self.github.repositories(installation_id)]
        except HTTPError as error:
            raise ValueError(
                "GitHub repository list is unavailable, expired, or missing permissions"
            ) from error

    def github_branches(
        self, principal: Principal, installation_id: str, repository: str
    ) -> list[str]:
        del principal
        try:
            return self.github.branches(installation_id, repository)
        except HTTPError as error:
            raise ValueError(
                "GitHub branch list is unavailable, expired, or missing permissions"
            ) from error

    def disconnect_project_repository(self, principal: Principal, project_id: str) -> None:
        project = self._project(principal, project_id)
        self.db.query(RepositoryConnection).filter(
            RepositoryConnection.project_id == project.id,
            RepositoryConnection.organization_id == principal.organization_id,
        ).delete(synchronize_session=False)
        project.repository_url = None
        self.audit(principal, "repository.disconnected", "project", project.id, {})
        self.db.commit()

    def repository_discovery(self, principal: Principal, project_id: str) -> dict[str, Any]:
        project = self._project(principal, project_id)
        if not project.repository_url:
            raise ValueError("project has no repository connection")
        installation_id = getattr(self.github, "installation_id", "fixture-installation")
        connection = self.db.scalar(
            select(RepositoryConnection).where(RepositoryConnection.project_id == project.id)
        )
        selected_branch = connection.selected_branch if connection else None
        analysis = self.github.analyze_repository(
            installation_id, project.repository_url, selected_branch
        )
        metadata = self.github.inspect_repository(
            installation_id, project.repository_url, selected_branch
        )
        execution = getattr(self.github, "execution", "SIMULATED")
        stored = StoredRepositoryAnalysis(
            organization_id=principal.organization_id,
            project_id=project.id,
            repository_url=project.repository_url,
            selected_branch=analysis.selected_branch,
            execution=execution,
            analysis=self._repository_analysis_payload(analysis),
        )
        self.db.add(stored)
        self.audit(
            principal,
            "repository.analyzed",
            "project",
            project.id,
            {
                "provider": metadata.provider,
                "repository": metadata.repository,
                "branch": analysis.selected_branch,
                "execution": execution,
                "manifests": list(analysis.manifests),
            },
        )
        self.db.commit()
        return metadata.__dict__ | {
            "execution": execution,
            "selected_branch": analysis.selected_branch,
            "analysis": stored.analysis,
        }

    @staticmethod
    def _repository_analysis_payload(analysis: object) -> dict[str, Any]:
        payload = analysis.__dict__.copy()
        for key, value in payload.items():
            if isinstance(value, tuple):
                payload[key] = list(value)
        return payload

    def latest_repository_analysis(
        self, principal: Principal, project_id: str
    ) -> StoredRepositoryAnalysis | None:
        project = self._project(principal, project_id)
        return self.db.scalar(
            select(StoredRepositoryAnalysis)
            .where(
                StoredRepositoryAnalysis.organization_id == principal.organization_id,
                StoredRepositoryAnalysis.project_id == project.id,
            )
            .order_by(StoredRepositoryAnalysis.created_at.desc())
            .limit(1)
        )

    def desired_state_publication(
        self, principal: Principal, project_id: str, plan_id: str
    ) -> dict[str, object]:
        """Shape a reviewed desired-state PR without contacting GitHub."""
        project = self._project(principal, project_id)
        plan = self._plan(principal, plan_id)
        if plan.action != PlanAction.DEPLOY or plan.state != LifecycleState.APPROVED:
            raise ValueError("only an approved deployment plan can publish desired state")
        intent = self._intent(principal, plan.intent_id)
        if intent.project_id != project.id or not project.repository_url:
            raise PermissionError("plan does not belong to a repository-connected project")
        publication = self.github.publish_reviewed_desired_state(
            "fixture-installation",
            project.repository_url,
            f"agentconstruct/{plan.id}.json",
            json.dumps(plan.payload, sort_keys=True),
        )
        self.audit(
            principal,
            "gitops.desired_state_contract_created",
            "deployment_plan",
            plan.id,
            {"profile": plan.payload["architecture"]["profile"]},
        )
        self.db.commit()
        return publication.__dict__ | {
            "execution": "SIMULATED",
            "profile": plan.payload["architecture"]["profile"],
        }

    def create_desired_state_publication_for_revision(
        self, principal: Principal, revision_id: str, provided_digest: str
    ) -> dict[str, Any]:
        """Create a fixture reviewed-PR publication for an approved customer plan.

        This is the product contract for later GitHub writes. It persists the
        package and PR state locally, but the current adapter still returns a
        fixture URL and never contacts GitHub.
        """
        revision, infrastructure_plan, source_deployment = self._approved_customer_revision(
            principal, revision_id
        )
        if revision.content_digest != provided_digest or plan_hash(revision.content) != provided_digest:
            raise ValueError("stale desired-state publication: approved digest changed")
        project = self._project(principal, infrastructure_plan.project_id)
        content = revision.content
        application = content.get("application_analysis") or {}
        repository_url = application.get("repository")
        branch = application.get("branch")
        if not repository_url or not branch:
            raise ValueError("approved plan has no selected repository and branch")
        repository_connection = self.db.scalar(
            select(RepositoryConnection).where(
                RepositoryConnection.organization_id == principal.organization_id,
                RepositoryConnection.project_id == project.id,
                RepositoryConnection.repository_url == repository_url,
            )
        )
        if repository_connection is None:
            raise ValueError("selected repository is no longer connected to this project")
        if repository_connection.selected_branch and repository_connection.selected_branch != branch:
            raise ValueError("selected repository branch changed after approval")
        self._assert_github_installation_publishable(principal)
        existing = self.db.scalar(
            select(DesiredStatePublication).where(
                DesiredStatePublication.organization_id == principal.organization_id,
                DesiredStatePublication.revision_id == revision.id,
                DesiredStatePublication.content_digest == revision.content_digest,
            )
        )
        if existing:
            return self._desired_state_publication_payload(existing)
        package = self._desired_state_package(
            revision=revision,
            infrastructure_plan=infrastructure_plan,
            source_deployment=source_deployment,
            repository_url=str(repository_url),
            branch=str(branch),
        )
        publication = self.github.publish_reviewed_desired_state(
            "fixture-installation",
            str(repository_url),
            f"agentconstruct/{revision.id}/desired-state-package.json",
            json.dumps(package, sort_keys=True),
        )
        stored = DesiredStatePublication(
            organization_id=principal.organization_id,
            revision_id=revision.id,
            project_id=project.id,
            repository_url=str(repository_url),
            branch=str(branch),
            state="PUBLISHED",
            publication_url=publication.pull_request_url,
            required_checks={"checks": list(publication.required_checks)},
            package=package,
            content_digest=revision.content_digest,
            created_by_subject=principal.subject,
        )
        self.db.add(stored)
        self.db.flush()
        self.audit(
            principal,
            "desired_state.fixture_pr_published",
            "desired_state_publication",
            stored.id,
            {
                "revision_id": revision.id,
                "digest": revision.content_digest,
                "profile": package["profile"],
                "state": stored.state,
                "boundary": "fixture PR only; AgentConstruct cannot merge or write live GitHub content",
            },
        )
        self.db.commit()
        return self._desired_state_publication_payload(stored)

    def _assert_github_installation_publishable(self, principal: Principal) -> None:
        blocked_states = {"REVOKED", "SUSPENDED", "MISSING_PERMISSION", "REPOSITORY_INACCESSIBLE"}
        state = self.db.scalar(
            select(GitHubAppInstallationState)
            .where(GitHubAppInstallationState.organization_id == principal.organization_id)
            .order_by(GitHubAppInstallationState.updated_at.desc())
            .limit(1)
        )
        if state and state.state in blocked_states:
            raise PermissionError(f"GitHub App installation is not publishable: {state.state}")

    def update_desired_state_publication_state(
        self,
        principal: Principal,
        revision_id: str,
        publication_id: str,
        *,
        content_digest: str,
        state: str,
    ) -> dict[str, Any]:
        """Record local fixture PR/check state for the approved desired-state package.

        This models a human-reviewed PR/check result in local mode. It never
        writes GitHub, never merges, and never deploys.
        """
        if not self._is_workspace_administrator(principal):
            raise PermissionError("only a workspace administrator can update fixture PR review state")
        revision, _, _ = self._approved_customer_revision(principal, revision_id)
        if revision.content_digest != content_digest or plan_hash(revision.content) != content_digest:
            raise ValueError("stale desired-state state update: approved digest changed")
        publication = self.db.get(DesiredStatePublication, publication_id)
        if (
            publication is None
            or publication.organization_id != principal.organization_id
            or publication.revision_id != revision.id
            or publication.content_digest != revision.content_digest
        ):
            raise PermissionError("desired-state publication not found for this approved revision")
        allowed = {
            "PUBLISHED": {"CHECKS_PENDING", "CHECKS_PASSED", "CLOSED"},
            "CHECKS_PENDING": {"CHECKS_PASSED", "CLOSED"},
            "CHECKS_PASSED": {"CLOSED"},
            "CLOSED": set(),
            "MERGED": set(),
        }
        if state not in allowed.get(publication.state, set()):
            raise ValueError(f"cannot change fixture PR state from {publication.state} to {state}")
        publication.state = state
        self.audit(
            principal,
            "desired_state.fixture_pr_state_recorded",
            "desired_state_publication",
            publication.id,
            {
                "revision_id": revision.id,
                "digest": revision.content_digest,
                "state": state,
                "boundary": "local fixture PR/check state only; no GitHub write, merge or deployment",
            },
        )
        self.db.commit()
        return self._desired_state_publication_payload(publication)

    def _desired_state_package(
        self,
        *,
        revision: InfrastructurePlanRevision,
        infrastructure_plan: InfrastructurePlan,
        source_deployment: DeploymentPlan,
        repository_url: str,
        branch: str,
    ) -> dict[str, Any]:
        content = revision.content
        profile_name = content["summary"]["selected_profile"]
        profile = execution_profile(profile_name)
        target = content.get("target") or {}
        observability = content.get("observability") or {}
        common = {
            "revision_id": revision.id,
            "plan_id": infrastructure_plan.id,
            "source_deployment_plan_id": source_deployment.id,
            "approved_digest": revision.content_digest,
            "profile": profile_name,
            "repository": repository_url,
            "branch": branch,
            "target": target,
            "required_tags": {
                "ManagedBy": "AgentConstruct",
                "AgentConstructPlanDigest": revision.content_digest,
                "AgentConstructProjectId": infrastructure_plan.project_id,
            },
            "observability": observability,
            "execution_boundary": (
                "Desired-state fixture only. It requires human PR review and does not apply "
                "Terraform, merge GitHub changes or deploy cloud resources."
            ),
        }
        contract = {
            "kind": "agentconstruct.desired-state-package.v1",
            **common,
            "delivery": {
                "kind": profile.delivery_kind,
                "terraform_boundary": profile.terraform_boundary,
                "gitops_boundary": profile.gitops_boundary,
                "kubernetes_boundary": profile.kubernetes_boundary,
            },
            "files": [
                {
                    "path": "agentconstruct/approved-plan.json",
                    "purpose": "Exact approved customer-plan revision and digest binding.",
                    "content": {
                        "revision_id": revision.id,
                        "digest": revision.content_digest,
                        "content": content,
                    },
                },
                {
                    "path": f"infrastructure/{profile_name}/contract.json",
                    "purpose": f"Profile-specific {profile.delivery_kind} deployment contract.",
                    "content": self._profile_desired_state_contract(profile_name, common),
                },
                {
                    "path": "agentconstruct/README.md",
                    "purpose": "Human review note for the fixture PR.",
                    "content": (
                        "# AgentConstruct desired state\n\n"
                        "This fixture package is generated from an approved plan. "
                        "It is not applied, merged, or executed by AgentConstruct."
                    ),
                },
            ],
            "pr_state_model": [
                "NOT_CREATED",
                "READY_TO_PUBLISH",
                "PUBLISHED",
                "CHECKS_PENDING",
                "CHECKS_PASSED",
                "MERGED",
                "CLOSED",
            ],
            "merge_boundary": "AgentConstruct records PR state but never merges customer code or desired state.",
        }
        return contract

    @staticmethod
    def _profile_desired_state_contract(profile_name: str, common: dict[str, Any]) -> dict[str, Any]:
        if profile_name == "aws-app-runner":
            return {
                "profile": profile_name,
                "resources": ["aws_apprunner_service", "aws_iam_role", "aws_secretsmanager_secret_reference"],
                "source": "container image or repository source resolved by a later reviewed pipeline",
                "networking": "managed HTTPS ingress with private data/service boundaries where supported",
                "monitoring": common["observability"],
                "tags": common["required_tags"],
            }
        if profile_name == "aws-ecs-fargate":
            return {
                "profile": profile_name,
                "resources": ["aws_ecs_service", "aws_ecs_task_definition", "aws_lb", "aws_iam_role"],
                "source": "immutable image digest from an approved build",
                "networking": "private subnets with narrowly scoped load balancer ingress when required",
                "monitoring": common["observability"],
                "tags": common["required_tags"],
            }
        if profile_name == "aws-eks-governed":
            return {
                "profile": profile_name,
                "resources": ["helm_release", "kubernetes_namespace", "argocd_application"],
                "gitops": "reviewed desired state only; Argo observes after human merge",
                "kubernetes_required": True,
                "monitoring": common["observability"],
                "tags": common["required_tags"],
            }
        return {
            "profile": profile_name,
            "resources": ["profile_specific_contract_pending"],
            "monitoring": common["observability"],
            "tags": common["required_tags"],
            "boundary": "Profile is recognized by the planner but cloud rendering remains plan-only.",
        }

    @staticmethod
    def _desired_state_publication_payload(publication: DesiredStatePublication) -> dict[str, Any]:
        return {
            "id": publication.id,
            "revision_id": publication.revision_id,
            "repository_url": publication.repository_url,
            "branch": publication.branch,
            "state": publication.state,
            "publication_url": publication.publication_url,
            "required_checks": publication.required_checks.get("checks", []),
            "package": publication.package,
            "content_digest": publication.content_digest,
            "created_by_subject": publication.created_by_subject,
            "created_at": publication.created_at.isoformat() if publication.created_at else None,
            "execution": "SIMULATED_FIXTURE_PR",
            "merge_boundary": "AgentConstruct never merges the desired-state PR itself.",
        }

    def create_terraform_plan_render_for_revision(
        self, principal: Principal, revision_id: str, provided_digest: str
    ) -> dict[str, Any]:
        """Generate a plan-only App Runner Terraform contract.

        This is a renderer, not an executor. It persists deterministic module
        inputs and file previews for human review and offline validation. It
        never returns an apply command and it never calls AWS.
        """
        revision, infrastructure_plan, source_deployment = self._approved_customer_revision(
            principal, revision_id
        )
        if revision.content_digest != provided_digest or plan_hash(revision.content) != provided_digest:
            raise ValueError("stale Terraform render request: approved digest changed")
        content = revision.content
        profile_name = str(content.get("summary", {}).get("selected_profile") or "")
        if profile_name != "aws-app-runner":
            raise ValueError("App Runner Terraform renderer only supports aws-app-runner approved plans")
        project = self._project(principal, infrastructure_plan.project_id)
        application = content.get("application_analysis") or {}
        target = content.get("target") or {}
        repository_url = application.get("repository")
        branch = application.get("branch")
        if not repository_url or not branch:
            raise ValueError("approved plan has no selected repository and branch")
        if target.get("provider") != "aws" or not target.get("region"):
            raise ValueError("approved plan has no AWS target region")
        repository_connection = self.db.scalar(
            select(RepositoryConnection).where(
                RepositoryConnection.organization_id == principal.organization_id,
                RepositoryConnection.project_id == project.id,
                RepositoryConnection.repository_url == repository_url,
            )
        )
        if repository_connection is None:
            raise ValueError("selected repository is no longer connected to this project")
        if repository_connection.selected_branch and repository_connection.selected_branch != branch:
            raise ValueError("selected repository branch changed after approval")
        existing = self.db.scalar(
            select(TerraformPlanRender).where(
                TerraformPlanRender.organization_id == principal.organization_id,
                TerraformPlanRender.revision_id == revision.id,
                TerraformPlanRender.content_digest == revision.content_digest,
                TerraformPlanRender.profile == profile_name,
            )
        )
        if existing:
            return self._terraform_plan_render_payload(existing)
        render = self._app_runner_terraform_contract(
            revision=revision,
            infrastructure_plan=infrastructure_plan,
            source_deployment=source_deployment,
            repository_url=str(repository_url),
            branch=str(branch),
        )
        stored = TerraformPlanRender(
            organization_id=principal.organization_id,
            revision_id=revision.id,
            project_id=project.id,
            profile=profile_name,
            state="PLAN_ONLY_NOT_APPLIED",
            terraform_root=render["terraform_root"],
            module_path=render["module_path"],
            render=render,
            content_digest=revision.content_digest,
            created_by_subject=principal.subject,
        )
        self.db.add(stored)
        self.db.flush()
        self.audit(
            principal,
            "terraform.plan_only_contract_rendered",
            "terraform_plan_render",
            stored.id,
            {
                "revision_id": revision.id,
                "digest": revision.content_digest,
                "profile": profile_name,
                "status": stored.state,
                "boundary": "plan-only Terraform contract; no plan/apply/destroy command executed",
            },
        )
        self.db.commit()
        return self._terraform_plan_render_payload(stored)

    def _app_runner_terraform_contract(
        self,
        *,
        revision: InfrastructurePlanRevision,
        infrastructure_plan: InfrastructurePlan,
        source_deployment: DeploymentPlan,
        repository_url: str,
        branch: str,
    ) -> dict[str, Any]:
        content = revision.content
        profile = execution_profile("aws-app-runner")
        target = content.get("target") or {}
        observability = content.get("observability") or {}
        workload = content.get("application_analysis", {}).get("workload_spec", {})
        resource_names = [
            resource.get("name", "")
            for resource in content.get("resource_breakdown", [])
        ]
        if any("eks" in name.lower() or "kubernetes" in name.lower() for name in resource_names):
            raise ValueError("unsupported resources for App Runner renderer")
        service_name = self._terraform_safe_name(infrastructure_plan.title)
        digest = revision.content_digest
        account_id = target.get("account_id") or "customer-account-selected-at-apply-time"
        module_inputs = {
            "project_id": infrastructure_plan.project_id,
            "revision_id": revision.id,
            "source_deployment_plan_id": source_deployment.id,
            "plan_digest": digest,
            "profile": "aws-app-runner",
            "service_name": service_name,
            "repository_url": repository_url,
            "repository_branch": branch,
            "aws_account_id": account_id,
            "aws_region": target["region"],
            "source_boundary": (
                "Plan-only contract expects a later reviewed build to publish an immutable image "
                "to ECR or an explicitly approved App Runner source. This renderer does not build, "
                "push, deploy or grant GitHub write access."
            ),
            "image_repository": f"{account_id}.dkr.ecr.{target['region']}.amazonaws.com/{service_name}",
            "environment_variables": {
                "AGENTCONSTRUCT_PLAN_DIGEST": digest,
                "AGENTCONSTRUCT_PROFILE": "aws-app-runner",
                "APP_ENVIRONMENTS": ",".join(workload.get("environments") or []),
            },
            "secret_references": {
                "application": "aws-secretsmanager://agentconstruct/app-runner/application",
            },
            "https_access": {
                "ingress": "managed App Runner HTTPS endpoint",
                "custom_domain": "optional later Route 53/ACM contract",
                "private_data_boundary": "customer data remains in the selected AWS account",
            },
            "iam": {
                "runtime_role": "least-privilege App Runner instance role",
                "deployment_role": "future explicit execution role; unavailable in this local renderer",
            },
            "observability": {
                "metrics_backend": observability.get("metrics_backend"),
                "grafana": observability.get("dashboard"),
                "scrape_targets": observability.get("scrape_targets", []),
                "baseline_dashboard": observability.get("baseline_dashboard", {}),
                "access_boundary": observability.get("access_boundary"),
                "limitations": observability.get("limitations", []),
                "cost_assumption": observability.get("cost_assumption"),
            },
            "tags": {
                "ManagedBy": "AgentConstruct",
                "AgentConstructPlanDigest": digest,
                "AgentConstructProjectId": infrastructure_plan.project_id,
                "AgentConstructRevisionId": revision.id,
                "AgentConstructProfile": "aws-app-runner",
            },
        }
        return {
            "kind": "agentconstruct.terraform.plan-only-render.v1",
            "profile": profile.profile,
            "delivery_kind": profile.delivery_kind,
            "status": "PLAN_ONLY_NOT_APPLIED",
            "execution_boundary": (
                "Generated deployment contract only. It is not a Terraform plan, apply, destroy, "
                "AWS API call, GitHub write, Kubernetes action or production deployment."
            ),
            "terraform_root": "infrastructure/terraform/renderers/app-runner-plan",
            "module_path": "infrastructure/terraform/modules/app-runner-plan-contract",
            "commands": [
                "terraform fmt -check -recursive infrastructure/terraform",
                "terraform -chdir=infrastructure/terraform/renderers/app-runner-plan init -backend=false -input=false",
                "terraform -chdir=infrastructure/terraform/renderers/app-runner-plan validate",
            ],
            "apply_command_available": False,
            "module_inputs": module_inputs,
            "files": [
                {
                    "path": "main.tf.json",
                    "purpose": "Root module wrapper for offline validation.",
                    "content": {
                        "module": {
                            "agentconstruct_app_runner_plan_contract": {
                                "source": "../../modules/app-runner-plan-contract",
                                **module_inputs,
                            }
                        }
                    },
                },
                {
                    "path": "terraform.tfvars.json",
                    "purpose": "Human-readable exact inputs generated from the approved digest.",
                    "content": module_inputs,
                },
                {
                    "path": "README.md",
                    "purpose": "Operator boundary note.",
                    "content": (
                        "# AgentConstruct App Runner plan-only Terraform contract\n\n"
                        "Generated from an approved customer-plan revision. Validate only; do not apply."
                    ),
                },
            ],
        }

    @staticmethod
    def _terraform_safe_name(value: str) -> str:
        safe = "".join(character.lower() if character.isalnum() else "-" for character in value)
        safe = "-".join(part for part in safe.split("-") if part)
        return safe[:48] or "agentconstruct-app"

    @staticmethod
    def _terraform_plan_render_payload(render: TerraformPlanRender) -> dict[str, Any]:
        return {
            "id": render.id,
            "revision_id": render.revision_id,
            "profile": render.profile,
            "state": render.state,
            "terraform_root": render.terraform_root,
            "module_path": render.module_path,
            "render": render.render,
            "content_digest": render.content_digest,
            "created_by_subject": render.created_by_subject,
            "created_at": render.created_at.isoformat() if render.created_at else None,
            "execution": "IMPLEMENTED_UNEXECUTED_PLAN_ONLY",
            "boundary": "No Terraform plan/apply/destroy or AWS mutation is reachable from this renderer.",
        }

    def create_cloud_readiness_preflight(
        self,
        principal: Principal,
        revision_id: str,
        *,
        content_digest: str,
        expected_account_id: str | None,
        allowed_regions: list[str],
        required_tags: dict[str, str],
        budget_ceiling_usd: int | None,
        execution_mode: str,
        require_reviewed_pr: bool,
        runtime_identity_configured: bool,
    ) -> dict[str, Any]:
        """Evaluate local guardrails before any future cloud action can be considered."""
        if not self._is_workspace_administrator(principal):
            raise PermissionError("only a workspace administrator can run cloud-readiness preflight")
        revision, infrastructure_plan, _ = self._approved_customer_revision(principal, revision_id)
        if revision.content_digest != content_digest or plan_hash(revision.content) != content_digest:
            raise ValueError("stale cloud preflight request: approved digest changed")
        content = revision.content
        target = content.get("target") or {}
        policy = content.get("policy_findings") or {}
        cost = content.get("cost_estimate", {}).get("range") or {}
        render = self.db.scalar(
            select(TerraformPlanRender)
            .where(
                TerraformPlanRender.organization_id == principal.organization_id,
                TerraformPlanRender.revision_id == revision.id,
                TerraformPlanRender.content_digest == revision.content_digest,
            )
            .order_by(TerraformPlanRender.created_at.desc())
            .limit(1)
        )
        publication = self.db.scalar(
            select(DesiredStatePublication)
            .where(
                DesiredStatePublication.organization_id == principal.organization_id,
                DesiredStatePublication.revision_id == revision.id,
                DesiredStatePublication.content_digest == revision.content_digest,
            )
            .order_by(DesiredStatePublication.created_at.desc())
            .limit(1)
        )
        module_inputs = (render.render.get("module_inputs") if render else {}) or {}
        render_tags = module_inputs.get("tags") or {}
        region = target.get("region")
        account_id = target.get("account_id")
        if not account_id and render:
            rendered_account = module_inputs.get("aws_account_id")
            account_id = None if rendered_account == "customer-account-selected-at-apply-time" else rendered_account
        checklist = [
            self._preflight_item(
                "approved_digest",
                "Exact approved digest",
                revision.content_digest == content_digest,
                f"approved digest {revision.content_digest}",
            ),
            self._preflight_item(
                "policy_result",
                "Policy allows future execution consideration",
                policy.get("result") != PolicyResult.DENY,
                f"policy result: {policy.get('result', 'unknown')}",
            ),
            self._preflight_item(
                "terraform_contract",
                "Generated Terraform contract",
                bool(render and render.state == "PLAN_ONLY_NOT_APPLIED"),
                "plan-only App Runner contract exists" if render else "no generated Terraform contract",
            ),
            self._preflight_item(
                "no_apply_command",
                "No apply command is reachable",
                bool(render and render.render.get("apply_command_available") is False),
                "renderer exposes validate-only commands" if render else "renderer missing",
            ),
            self._preflight_item(
                "expected_account",
                "Expected AWS account",
                expected_account_id is None or account_id == expected_account_id,
                f"expected {expected_account_id or 'not supplied'}; plan target {account_id or 'not connected'}",
            ),
            self._preflight_item(
                "allowed_region",
                "Allowed AWS region",
                bool(region and region in allowed_regions),
                f"region {region or 'missing'}; allowed {', '.join(allowed_regions)}",
            ),
            self._preflight_item(
                "required_tags",
                "Required ownership tags",
                all(render_tags.get(key) == value for key, value in required_tags.items()),
                f"required tags {required_tags or {'ManagedBy': 'AgentConstruct'}}",
            ),
            self._preflight_item(
                "budget_ceiling",
                "Budget ceiling",
                budget_ceiling_usd is None or int(cost.get("monthly_high", 0)) <= budget_ceiling_usd,
                f"estimated high ${cost.get('monthly_high', 'unknown')}; ceiling ${budget_ceiling_usd or 'not supplied'}",
            ),
            self._preflight_item(
                "reviewed_pr",
                "Reviewed desired-state PR",
                (not require_reviewed_pr) or bool(publication and publication.state in {"CHECKS_PASSED", "MERGED"}),
                f"state {publication.state if publication else 'not created'}",
            ),
            self._preflight_item(
                "runtime_identity",
                "AgentConstruct runtime identity",
                runtime_identity_configured,
                "not configured in local mode" if not runtime_identity_configured else "configured by operator",
            ),
            self._preflight_item(
                "execution_mode",
                "Dry-run/plan-only execution mode",
                execution_mode in {"DRY_RUN_ONLY", "PLAN_ONLY"},
                f"mode {execution_mode}; apply remains unavailable",
            ),
        ]
        failures = [item for item in checklist if item["status"] == "FAIL"]
        if not failures:
            state = "READY_FOR_AUTHORIZED_CLOUD_PLAN"
        elif all(item["id"] == "runtime_identity" for item in failures):
            state = "BLOCKED_CLOUD_RUNTIME_NOT_CONFIGURED"
        else:
            state = "BLOCKED_GUARDRAIL_FAILURE"
        guard = {
            "expected_account_id": expected_account_id,
            "allowed_regions": allowed_regions,
            "required_tags": required_tags,
            "budget_ceiling_usd": budget_ceiling_usd,
            "execution_mode": execution_mode,
            "require_reviewed_pr": require_reviewed_pr,
            "runtime_identity_configured": runtime_identity_configured,
        }
        would_deploy = {
            "profile": content.get("summary", {}).get("selected_profile"),
            "aws_account_id": account_id,
            "region": region,
            "terraform_root": render.terraform_root if render else None,
            "terraform_state": render.state if render else None,
            "desired_state_pr_state": publication.state if publication else None,
            "policy_result": policy.get("result"),
            "plan_digest": revision.content_digest,
            "not_deployed": True,
            "boundary": (
                "Preflight only. Cloud execution remains blocked unless a future explicit "
                "operator workflow performs an authenticated plan and a separately approved apply."
            ),
        }
        stored = CloudReadinessPreflight(
            organization_id=principal.organization_id,
            revision_id=revision.id,
            project_id=infrastructure_plan.project_id,
            state=state,
            guard=guard,
            checklist={"items": checklist},
            would_deploy=would_deploy,
            content_digest=revision.content_digest,
            created_by_subject=principal.subject,
        )
        self.db.add(stored)
        self.db.flush()
        self.audit(
            principal,
            "cloud_readiness.preflight_evaluated",
            "cloud_readiness_preflight",
            stored.id,
            {"revision_id": revision.id, "digest": revision.content_digest, "state": state},
        )
        self.db.commit()
        return self._cloud_readiness_preflight_payload(stored)

    @staticmethod
    def _preflight_item(check_id: str, label: str, passed: bool, detail: str) -> dict[str, str]:
        return {
            "id": check_id,
            "label": label,
            "status": "PASS" if passed else "FAIL",
            "detail": detail,
        }

    @staticmethod
    def _cloud_readiness_preflight_payload(preflight: CloudReadinessPreflight) -> dict[str, Any]:
        return {
            "id": preflight.id,
            "revision_id": preflight.revision_id,
            "state": preflight.state,
            "guard": preflight.guard,
            "checklist": preflight.checklist.get("items", []),
            "would_deploy": preflight.would_deploy,
            "content_digest": preflight.content_digest,
            "created_by_subject": preflight.created_by_subject,
            "created_at": preflight.created_at.isoformat() if preflight.created_at else None,
            "execution": "LOCAL_PREFLIGHT_ONLY",
            "boundary": "This preflight cannot run Terraform plan/apply/destroy or mutate AWS.",
        }

    def create_terraform_plan_review_for_revision(
        self,
        principal: Principal,
        revision_id: str,
        *,
        content_digest: str,
        preflight_id: str | None,
        expected_account_id: str | None,
        expected_region: str | None,
        mode: str,
        allow_cloud_plan: bool,
    ) -> dict[str, Any]:
        """Create plan-only Terraform review evidence.

        This is intentionally not an apply path. The default local mode records
        deterministic command evidence only. Authenticated plan mode is blocked
        unless both the request and process environment explicitly opt in.
        """
        if not self._is_workspace_administrator(principal):
            raise PermissionError("only a workspace administrator can request a Terraform plan review")
        revision, infrastructure_plan, _ = self._approved_customer_revision(principal, revision_id)
        if revision.content_digest != content_digest or plan_hash(revision.content) != content_digest:
            raise ValueError("stale Terraform plan review request: approved digest changed")
        render = self.db.scalar(
            select(TerraformPlanRender)
            .where(
                TerraformPlanRender.organization_id == principal.organization_id,
                TerraformPlanRender.revision_id == revision.id,
                TerraformPlanRender.content_digest == revision.content_digest,
                TerraformPlanRender.profile == "aws-app-runner",
            )
            .order_by(TerraformPlanRender.created_at.desc())
            .limit(1)
        )
        preflight_query = select(CloudReadinessPreflight).where(
            CloudReadinessPreflight.organization_id == principal.organization_id,
            CloudReadinessPreflight.revision_id == revision.id,
            CloudReadinessPreflight.content_digest == revision.content_digest,
        )
        if preflight_id:
            preflight_query = preflight_query.where(CloudReadinessPreflight.id == preflight_id)
        preflight = self.db.scalar(
            preflight_query.order_by(CloudReadinessPreflight.created_at.desc()).limit(1)
        )
        state = "PLAN_REVIEW_READY"
        blockers: list[str] = []
        evidence: dict[str, Any] = {
            "mode": mode,
            "profile": "aws-app-runner",
            "apply_available": False,
            "requested_authenticated_plan": mode == "AUTHENTICATED_TERRAFORM_PLAN",
            "execution_boundary": (
                "Plan-only review evidence. Terraform apply/destroy is unavailable and no AWS "
                "resource creation is reachable from this endpoint."
            ),
        }
        command = {
            "terraform_root": render.terraform_root if render else None,
            "commands": [],
            "apply_command_available": False,
            "executor": "fixture-plan-review",
        }
        if render is None:
            state = "BLOCKED_TERRAFORM_CONTRACT_REQUIRED"
            blockers.append("Generate an App Runner Terraform contract for the approved digest first.")
        else:
            render_inputs = render.render.get("module_inputs", {})
            region = render_inputs.get("aws_region")
            account_id = render_inputs.get("aws_account_id")
            command["commands"] = [
                f"terraform -chdir={render.terraform_root} init -backend=false -input=false",
                f"terraform -chdir={render.terraform_root} plan -input=false -refresh=false -lock=false -no-color",
            ]
            evidence.update(
                {
                    "terraform_render_id": render.id,
                    "terraform_root": render.terraform_root,
                    "module_path": render.module_path,
                    "plan_digest_embedded": render_inputs.get("plan_digest") == revision.content_digest,
                    "aws_account_id": account_id,
                    "aws_region": region,
                }
            )
            if expected_account_id and account_id not in {expected_account_id, "customer-account-selected-at-apply-time"}:
                state = "BLOCKED_ACCOUNT_GUARD"
                blockers.append(f"Expected AWS account {expected_account_id}; render targets {account_id}.")
            if expected_region and region != expected_region:
                state = "BLOCKED_REGION_GUARD"
                blockers.append(f"Expected AWS region {expected_region}; render targets {region}.")
        if preflight is None:
            state = "BLOCKED_PREFLIGHT_REQUIRED"
            blockers.append("Run a cloud-readiness preflight for this approved digest first.")
        elif preflight.state != "READY_FOR_AUTHORIZED_CLOUD_PLAN":
            state = "BLOCKED_PREFLIGHT"
            blockers.append(f"Cloud-readiness preflight is {preflight.state}.")
            evidence["preflight"] = self._cloud_readiness_preflight_payload(preflight)
        else:
            evidence["preflight"] = self._cloud_readiness_preflight_payload(preflight)
        if mode == "AUTHENTICATED_TERRAFORM_PLAN":
            env_allowed = os.getenv("ALLOW_CLOUD_PLAN", "").lower() == "true"
            if not allow_cloud_plan or not env_allowed:
                state = "BLOCKED_CLOUD_PLAN_NOT_ALLOWED"
                blockers.append("Authenticated Terraform plan requires request allow_cloud_plan=true and ALLOW_CLOUD_PLAN=true.")
            command["executor"] = "authenticated-terraform-plan-gated"
            evidence["allow_cloud_plan_request"] = allow_cloud_plan
            evidence["allow_cloud_plan_env"] = env_allowed
        else:
            evidence["fixture_plan_summary"] = (
                "Local contract review only. Commands are recorded as the only allowed plan-only "
                "shape; they are not an authenticated AWS plan and they never include apply."
            )
        if state == "PLAN_REVIEW_READY":
            state = (
                "AUTHENTICATED_PLAN_ALLOWED_NOT_EXECUTED"
                if mode == "AUTHENTICATED_TERRAFORM_PLAN"
                else "LOCAL_CONTRACT_PLAN_REVIEWED"
            )
            evidence["result"] = "ready for operator-authenticated terraform plan command outside automated tests"
        evidence["blockers"] = blockers
        stored = TerraformPlanReview(
            organization_id=principal.organization_id,
            revision_id=revision.id,
            project_id=infrastructure_plan.project_id,
            terraform_render_id=render.id if render else None,
            preflight_id=preflight.id if preflight else None,
            mode=mode,
            state=state,
            command=command,
            evidence=evidence,
            content_digest=revision.content_digest,
            created_by_subject=principal.subject,
        )
        self.db.add(stored)
        self.db.flush()
        self.audit(
            principal,
            "terraform.plan_only_review_recorded",
            "terraform_plan_review",
            stored.id,
            {
                "revision_id": revision.id,
                "digest": revision.content_digest,
                "state": state,
                "mode": mode,
                "apply_available": False,
            },
        )
        self.db.commit()
        return self._terraform_plan_review_payload(stored)

    @staticmethod
    def _terraform_plan_review_payload(review: TerraformPlanReview) -> dict[str, Any]:
        return {
            "id": review.id,
            "revision_id": review.revision_id,
            "terraform_render_id": review.terraform_render_id,
            "preflight_id": review.preflight_id,
            "mode": review.mode,
            "state": review.state,
            "command": review.command,
            "evidence": review.evidence,
            "content_digest": review.content_digest,
            "created_by_subject": review.created_by_subject,
            "created_at": review.created_at.isoformat() if review.created_at else None,
            "apply_available": False,
            "execution": "PLAN_ONLY_REVIEW_NO_APPLY",
            "boundary": "Terraform apply/destroy is unavailable. This record does not create AWS resources.",
        }

    def cloud_role_contract(self, principal: Principal, connection_id: str) -> dict[str, str | int]:
        connection = self.db.get(CloudConnection, connection_id)
        if not connection or connection.organization_id != principal.organization_id:
            raise PermissionError("cloud connection not found in this organization")
        return self.cloud_discovery.role_contract(connection.id).__dict__ | {"execution": "SIMULATED"}

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
            return self._create_intent(
                principal,
                project_id,
                prompt,
                source_repository,
                cloud_connection_id,
                idempotency_key,
            )

    def _create_intent(
        self,
        principal: Principal,
        project_id: str,
        prompt: str,
        source_repository: str | None,
        cloud_connection_id: str | None,
        idempotency_key: str,
    ) -> WorkloadIntent:
        project = self._project(principal, project_id)
        if cloud_connection_id:
            connection = self.db.get(CloudConnection, cloud_connection_id)
            if not connection or connection.organization_id != principal.organization_id:
                raise PermissionError("cloud connection not found in this organization")
        existing = self.db.scalar(
            select(WorkloadIntent).where(
                WorkloadIntent.organization_id == principal.organization_id,
                WorkloadIntent.idempotency_key == idempotency_key,
            )
        )
        if existing:
            if existing.prompt != prompt or existing.project_id != project_id:
                raise ValueError("idempotency key conflicts with a different request")
            return existing
        selected_repository = source_repository or project.repository_url
        interpretation = self.intent_provider.interpret(prompt, selected_repository)
        spec = interpretation.spec
        repository_analysis = self.latest_repository_analysis(principal, project.id)
        spec_payload = spec.model_dump(mode="json")
        if repository_analysis:
            repository_runtime = self._runtime_from_repository(repository_analysis.analysis)
            spec_payload["repository_analysis"] = repository_analysis.analysis
            if repository_runtime and spec_payload.get("runtime") in {None, "containerized"}:
                spec_payload["runtime"] = repository_runtime
            spec_payload["containerized"] = bool(
                spec_payload.get("containerized")
                or "containerized" in repository_analysis.analysis.get("runtime_hints", [])
                or "Dockerfile" in repository_analysis.analysis.get("manifests", [])
            )
            if repository_analysis.analysis.get("database_hints"):
                spec_payload["stateful"] = True
        state = LifecycleState.NEEDS_INPUT if spec.unknowns else LifecycleState.PLANNED
        intent = WorkloadIntent(
            organization_id=principal.organization_id,
            project_id=project.id,
            requester_subject=principal.subject,
            prompt=prompt,
            idempotency_key=idempotency_key,
            state=state,
            spec={
                **spec_payload,
                "cloud_connection_id": cloud_connection_id,
                "questions": [question.model_dump() for question in interpretation.questions],
            },
        )
        self.db.add(intent)
        self.db.flush()
        self.audit(
            principal,
            "intent.interpreted",
            "workload_intent",
            intent.id,
            {"state": state, "unknowns": spec.unknowns},
        )
        self.db.commit()
        return intent

    @staticmethod
    def _runtime_from_repository(analysis: dict[str, Any]) -> str | None:
        hints = analysis.get("framework_hints", []) + analysis.get("runtime_hints", [])
        if "fastapi" in hints:
            return "python-fastapi"
        if "django" in hints:
            return "python-django"
        if "next" in hints:
            return "node-nextjs"
        if "node" in hints:
            return "node"
        if "python" in hints:
            return "python"
        return None

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
        connection_id = str(intent.spec.get("cloud_connection_id") or "local-aws-fixture")
        requested_region = spec.region_constraints[0] if spec.region_constraints else "us-east-1"
        inventory = self.cloud_discovery.inventory(connection_id, requested_region)
        architecture = self.planner.plan(spec, inventory)
        stored = self.db.scalar(
            select(StoredArchitecturePlan).where(StoredArchitecturePlan.intent_id == intent.id)
        )
        if not stored:
            stored = StoredArchitecturePlan(
                organization_id=principal.organization_id,
                intent_id=intent.id,
                plan=architecture.model_dump(mode="json"),
            )
            self.db.add(stored)
        with self._trace("agentconstruct.policy.evaluate"):
            decision = self.policy.evaluate(principal, spec, PlanAction.DEPLOY)
        payload = {
            "action": PlanAction.DEPLOY,
            "intent_id": intent.id,
            "cloud_connection_id": intent.spec.get("cloud_connection_id"),
            "spec": spec.model_dump(mode="json"),
            "architecture": architecture.model_dump(mode="json"),
            "inventory": inventory.model_dump(mode="json"),
            "policy": {"result": decision.result, "reason": decision.reason},
        }
        digest = plan_hash(payload)
        existing = self.db.scalar(select(DeploymentPlan).where(DeploymentPlan.plan_hash == digest))
        if existing:
            return existing
        state = {
            PolicyResult.ALLOW: LifecycleState.PLANNED,
            PolicyResult.DENY: LifecycleState.POLICY_DENIED,
            PolicyResult.APPROVAL_REQUIRED: LifecycleState.APPROVAL_REQUIRED,
        }[decision.result]
        plan = DeploymentPlan(
            organization_id=principal.organization_id,
            intent_id=intent.id,
            requester_subject=principal.subject,
            action=PlanAction.DEPLOY,
            state=state,
            plan_hash=digest,
            policy_result=decision.result,
            payload=payload,
        )
        self.db.add(plan)
        intent.state = state
        self.db.flush()
        self.audit(
            principal,
            "deployment_plan.created",
            "deployment_plan",
            plan.id,
            {"hash": digest, "policy": decision.result, "reason": decision.reason},
        )
        self.db.commit()
        return plan

    def _plan(self, principal: Principal, plan_id: str) -> DeploymentPlan:
        plan = self.db.get(DeploymentPlan, plan_id)
        if not plan or plan.organization_id != principal.organization_id:
            raise PermissionError("deployment plan not found in this organization")
        return plan

    def get_plan(self, principal: Principal, plan_id: str) -> DeploymentPlan:
        return self._plan(principal, plan_id)

    def create_customer_plan_review(
        self, principal: Principal, deployment_plan_id: str
    ) -> InfrastructurePlanRevision:
        """Create the customer-facing DRAFT review from one validated AWS recommendation.

        The source deployment plan remains an execution contract. This separate business
        plan is intentionally DRAFT and cannot cause any cloud mutation.
        """
        deployment = self._plan(principal, deployment_plan_id)
        if deployment.action != PlanAction.DEPLOY:
            raise ValueError("only an AWS deployment recommendation can create a customer review")
        intent = self._intent(principal, str(deployment.intent_id))
        project = self._project(principal, intent.project_id)
        architecture = deployment.payload["architecture"]
        repository = self.db.scalar(
            select(RepositoryConnection).where(
                RepositoryConnection.organization_id == principal.organization_id,
                RepositoryConnection.project_id == project.id,
            )
        )
        repository_analysis = self.latest_repository_analysis(principal, project.id)
        connection_id = deployment.payload.get("cloud_connection_id")
        target: dict[str, Any] = {
            "provider": "aws",
            "region": architecture["region"],
            "connection_id": connection_id,
            "account_id": None,
            "connection_status": "local planning fixture" if not connection_id else "selected",
        }
        inventory_snapshot: dict[str, Any] | None = None
        if connection_id:
            connection = self._cloud_connection(principal, str(connection_id))
            target.update(
                {
                    "account_id": connection.account_id,
                    "connection_status": connection.setup_state,
                    "discovery_role": connection.discovery_role_arn,
                }
            )
            snapshot = self.db.scalar(
                select(StoredCloudInventorySnapshot)
                .where(
                    StoredCloudInventorySnapshot.organization_id == principal.organization_id,
                    StoredCloudInventorySnapshot.cloud_connection_id == connection.id,
                )
                .order_by(StoredCloudInventorySnapshot.captured_at.desc())
                .limit(1)
            )
            if snapshot:
                inventory_snapshot = {
                    "id": snapshot.id,
                    "captured_at": snapshot.captured_at.isoformat(),
                    "provenance": snapshot.provenance,
                    "resources": snapshot.snapshot.get("approved_resources", []),
                }
        content = {
            "kind": "agentconstruct.aws.infrastructure-plan.review.v1",
            "source_deployment_plan_id": deployment.id,
            "summary": {
                "selected_profile": architecture["profile"],
                "why": architecture["recommendation_reason"],
                "status": "DRAFT — review only; not submitted, approved, or deployed",
            },
            "application_analysis": {
                "project": project.name,
                "repository": project.repository_url,
                "branch": repository.selected_branch if repository else None,
                "request": intent.prompt,
                "repository_analysis": repository_analysis.analysis
                if repository_analysis
                else deployment.payload["spec"].get("repository_analysis", {}),
                "workload_spec": deployment.payload["spec"],
            },
            "target": target,
            "inventory_snapshot": inventory_snapshot,
            "architecture": {
                "components": architecture["components"],
                "dependencies": architecture["dependencies"],
                "capacity": architecture["estimated_capacity"],
                "operational_characteristics": architecture["operational_characteristics"],
                "existing_resources_reused": architecture["existing_resources_reused"],
                "new_resources_required": architecture["new_resources_required"],
            },
            "resource_breakdown": architecture["components"],
            "security": deployment.payload["architecture"]["security_controls"],
            "observability": architecture["observability"],
            "cost_estimate": {
                "range": architecture["cost_estimate"],
                "components": architecture["cost_components"],
                "label": "Estimated monthly AWS cost; not an actual AWS bill.",
            },
            "deployment_strategy": {
                "steps": architecture["execution_steps"],
                "rollback": architecture["rollback_strategy"],
                "boundary": "Submission and approval make this review eligible for a later explicit execution action. This review does not deploy AWS infrastructure.",
            },
            "risks_and_limitations": architecture["risks"],
            "policy_findings": deployment.payload["policy"],
            "evidence": {
                "planner": "deterministic local fixture pricing and capability catalogue",
                "cloud": "read-only discovery snapshot when one is selected; no deployment permission",
                "execution": "unexecuted customer plan review",
            },
        }
        drafts = self.db.scalars(
            select(InfrastructurePlanRevision)
            .where(
                InfrastructurePlanRevision.organization_id == principal.organization_id,
                InfrastructurePlanRevision.state == InfrastructurePlanState.DRAFT,
            )
            .order_by(InfrastructurePlanRevision.created_at.desc())
        ).all()
        existing = next(
            (
                draft
                for draft in drafts
                if draft.content.get("source_deployment_plan_id") == deployment.id
            ),
            None,
        )
        if existing is not None:
            return existing
        return self.create_infrastructure_plan(
            principal, project.id, f"AWS plan for {project.name}", content
        )

    def approve(self, principal: Principal, plan_id: str, provided_hash: str) -> DeploymentPlan:
        with self._trace("agentconstruct.plan.approve"):
            return self._approve(principal, plan_id, provided_hash)

    def _approve(self, principal: Principal, plan_id: str, provided_hash: str) -> DeploymentPlan:
        plan = self._plan(principal, plan_id)
        if not self._is_workspace_administrator(principal):
            raise PermissionError("workspace administrator role required for approval")
        if plan.requester_subject == principal.subject:
            raise PermissionError("requester cannot approve their own protected plan")
        if plan.plan_hash != provided_hash:
            raise ValueError("stale approval: plan hash changed")
        if plan.state not in {
            LifecycleState.APPROVAL_REQUIRED,
            LifecycleState.DESTROY_APPROVAL_REQUIRED,
        }:
            raise ValueError("plan does not need approval")
        plan.state = LifecycleState.APPROVED
        self.db.add(
            Approval(
                deployment_plan_id=plan.id,
                plan_hash=plan.plan_hash,
                approver_subject=principal.subject,
            )
        )
        self.audit(
            principal,
            "deployment_plan.approved",
            "deployment_plan",
            plan.id,
            {"hash": plan.plan_hash},
        )
        self.db.commit()
        return plan

    def execute(self, principal: Principal, plan_id: str) -> list[Environment]:
        """Queue bounded work. A separate worker observes the fixture result."""
        plan = self._plan(principal, plan_id)
        if plan.action == PlanAction.DESTROY:
            return [self._queue_destroy(principal, plan)]
        if plan.action == PlanAction.CHANGE:
            return [self._queue_change(principal, plan)]
        if plan.state not in {LifecycleState.PLANNED, LifecycleState.APPROVED}:
            raise ValueError("plan is not executable")
        if plan.state == LifecycleState.APPROVED and not self.db.scalar(
            select(Approval).where(
                Approval.deployment_plan_id == plan.id, Approval.plan_hash == plan.plan_hash
            )
        ):
            raise ValueError("approved plan has no matching durable approval")
        spec = WorkloadSpec.model_validate(plan.payload["spec"])
        environments: list[Environment] = []
        plan.state = LifecycleState.QUEUED
        intent = self._intent(principal, plan.intent_id)
        for environment_type in spec.environments:
            environment = Environment(
                organization_id=principal.organization_id,
                project_id=intent.project_id,
                name=f"{intent.id[:8]}-{environment_type}",
                environment_type=environment_type,
                state=LifecycleState.QUEUED,
                desired_state={
                    "profile": plan.payload["architecture"]["profile"],
                    "execution_profile": execution_profile(
                        plan.payload["architecture"]["profile"]
                    ).__dict__,
                    "plan_hash": plan.plan_hash,
                    "execution_mode": plan.payload.get("execution_mode", "LOCAL_FIXTURE"),
                    "customer_plan_revision_id": plan.payload.get("customer_plan_revision_id"),
                    "customer_plan_digest": plan.payload.get("customer_plan_digest"),
                    "cost_estimate": plan.payload["architecture"].get("cost_estimate"),
                    "should_fail": "force failure" in intent.prompt.lower(),
                    "should_degrade": "force degraded" in intent.prompt.lower(),
                    "spec": plan.payload["spec"],
                    "min_replicas": 1,
                },
                observed_state={},
            )
            self.db.add(environment)
            self.db.flush()
            self.db.add(
                ExecutionJob(
                    deployment_plan_id=plan.id,
                    environment_id=environment.id,
                    state="QUEUED",
                    result={"operation": "DEPLOY"},
                )
            )
            self.audit(
                principal,
                "execution.queued",
                "environment",
                environment.id,
                {"plan_hash": plan.plan_hash},
            )
            environments.append(environment)
        self.db.commit()
        return environments

    def run_next_job(self) -> bool:
        """Run one durable fixture job. This is called only by the trusted local worker."""
        job = self.db.scalar(
            select(ExecutionJob)
            .where(ExecutionJob.state == "QUEUED")
            .order_by(ExecutionJob.created_at)
            .limit(1)
        )
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
                environment.state = (
                    LifecycleState.DESTROYED
                    if observation.state == "DESTROYED"
                    else LifecycleState.FAILED
                )
                action = (
                    "environment.destroyed"
                    if environment.state == LifecycleState.DESTROYED
                    else "environment.destroy_failed"
                )
            elif plan.action == PlanAction.CHANGE:
                for state in (
                    LifecycleState.PROVISIONING,
                    LifecycleState.DEPLOYING,
                    LifecycleState.VERIFYING,
                ):
                    require_transition(LifecycleState(environment.state), state)
                    environment.state = state
                change = plan.payload["recommendation"]["proposed_change"]
                observation = self.executor.change(environment.id, int(change["to"]))
                environment.desired_state = {
                    **environment.desired_state,
                    "min_replicas": int(change["to"]),
                    "last_change_plan_hash": plan.plan_hash,
                }
                environment.state = (
                    LifecycleState.READY if observation.state == "READY" else LifecycleState.FAILED
                )
                action = "environment.change_observed"
                self._resolve_day2_records(plan, environment)
            else:
                for state in (
                    LifecycleState.PROVISIONING,
                    LifecycleState.DEPLOYING,
                    LifecycleState.VERIFYING,
                ):
                    require_transition(LifecycleState(environment.state), state)
                    environment.state = state
                observation = self.executor.deploy(
                    environment.id,
                    profile=environment.desired_state["profile"],
                    should_fail=bool(environment.desired_state.get("should_fail")),
                    should_degrade=bool(environment.desired_state.get("should_degrade")),
                )
                environment.state = {
                    "READY": LifecycleState.READY,
                    "DEGRADED": LifecycleState.DEGRADED,
                }.get(observation.state, LifecycleState.FAILED)
                action = (
                    "environment.degraded"
                    if environment.state == LifecycleState.DEGRADED
                    else "environment.observed"
                )
                if environment.state == LifecycleState.DEGRADED:
                    self._open_incident(
                        environment,
                        "Fixture observation detected degraded application health.",
                        observation.detail,
                    )
            environment.observed_state = observation.detail
            self._record_environment_observation_assets(environment, observation.detail)
            job.state = (
                "SUCCEEDED" if observation.state in {"READY", "DEGRADED", "DESTROYED"} else "FAILED"
            )
            job.result = {"observation": observation.detail, "state": environment.state}
            principal = Principal(
                subject="system-worker",
                organization_id=environment.organization_id,
                role="operator",
            )
            self.audit(
                principal,
                action,
                "environment",
                environment.id,
                {"state": environment.state, "observation": observation.detail},
            )
            self.db.commit()
        return True

    def destroy_plan(self, principal: Principal, environment_id: str) -> DeploymentPlan:
        with self._trace("agentconstruct.destroy.plan"):
            return self._destroy_plan(principal, environment_id)

    def _destroy_plan(self, principal: Principal, environment_id: str) -> DeploymentPlan:
        environment = self._environment(principal, environment_id)
        if LifecycleState(environment.state) not in {
            LifecycleState.READY,
            LifecycleState.FAILED,
            LifecycleState.DEGRADED,
        }:
            raise ValueError("environment cannot be destroyed in its current state")
        environment.state = LifecycleState.DESTROY_REQUESTED
        requires_approval = environment.environment_type == EnvironmentName.PRODUCTION
        payload = {
            "action": PlanAction.DESTROY,
            "environment_id": environment.id,
            "observed_state": environment.observed_state,
        }
        digest = plan_hash(payload)
        plan = DeploymentPlan(
            organization_id=principal.organization_id,
            environment_id=environment.id,
            requester_subject=principal.subject,
            action=PlanAction.DESTROY,
            state=LifecycleState.DESTROY_APPROVAL_REQUIRED
            if requires_approval
            else LifecycleState.PLANNED,
            plan_hash=digest,
            policy_result=PolicyResult.APPROVAL_REQUIRED
            if requires_approval
            else PolicyResult.ALLOW,
            payload=payload,
        )
        self.db.add(plan)
        self.db.flush()
        self.audit(
            principal,
            "destroy_plan.created",
            "deployment_plan",
            plan.id,
            {"hash": digest, "approval_required": requires_approval},
        )
        self.db.commit()
        return plan

    def recommendation(self, principal: Principal, environment_id: str) -> dict[str, Any]:
        """Explain a bounded local Day-2 change; this does not mutate the environment."""
        with self._trace("agentconstruct.day2.diagnose"):
            environment = self._environment(principal, environment_id)
            if LifecycleState(environment.state) not in {LifecycleState.READY, LifecycleState.DEGRADED}:
                raise ValueError("environment must be ready or degraded before it can be diagnosed")
            record = self._recommendation_record(principal, environment)
            return self._recommendation_response(record)

    def change_plan(self, principal: Principal, environment_id: str) -> DeploymentPlan:
        with self._trace("agentconstruct.day2.change_plan"):
            environment = self._environment(principal, environment_id)
            if LifecycleState(environment.state) == LifecycleState.CHANGE_PROPOSED:
                existing = self.db.scalar(
                    select(DeploymentPlan)
                    .where(
                        DeploymentPlan.environment_id == environment.id,
                        DeploymentPlan.action == PlanAction.CHANGE,
                        DeploymentPlan.state.in_(
                            [LifecycleState.PLANNED, LifecycleState.APPROVAL_REQUIRED]
                        ),
                    )
                    .order_by(DeploymentPlan.created_at.desc())
                )
                if existing:
                    return existing
            if LifecycleState(environment.state) not in {LifecycleState.READY, LifecycleState.DEGRADED}:
                raise ValueError("environment cannot receive a change plan in its current state")
            record = self._recommendation_record(principal, environment)
            recommendation = record.recommendation
            spec = WorkloadSpec.model_validate(environment.desired_state["spec"])
            with self._trace("agentconstruct.policy.evaluate"):
                decision = self.policy.evaluate(
                    principal,
                    spec,
                    PlanAction.CHANGE,
                    target_environment_type=environment.environment_type,
                )
            payload = {
                "action": PlanAction.CHANGE,
                "environment_id": environment.id,
                "spec": spec.model_dump(mode="json"),
                "recommendation": recommendation,
                "recommendation_record_id": record.id,
                "policy": {"result": decision.result, "reason": decision.reason},
            }
            digest = plan_hash(payload)
            existing = self.db.scalar(select(DeploymentPlan).where(DeploymentPlan.plan_hash == digest))
            if existing:
                return existing
            state = {
                PolicyResult.ALLOW: LifecycleState.PLANNED,
                PolicyResult.DENY: LifecycleState.POLICY_DENIED,
                PolicyResult.APPROVAL_REQUIRED: LifecycleState.APPROVAL_REQUIRED,
            }[decision.result]
            plan = DeploymentPlan(
                organization_id=principal.organization_id,
                environment_id=environment.id,
                requester_subject=principal.subject,
                action=PlanAction.CHANGE,
                state=state,
                plan_hash=digest,
                policy_result=decision.result,
                payload=payload,
            )
            self.db.add(plan)
            self.db.flush()
            record.deployment_plan_id = plan.id
            if decision.result == PolicyResult.DENY:
                record.state = "DENIED"
            else:
                record.state = "PLANNED"
                require_transition(LifecycleState(environment.state), LifecycleState.CHANGE_PROPOSED)
                environment.state = LifecycleState.CHANGE_PROPOSED
            self.audit(
                principal,
                "change_plan.created",
                "deployment_plan",
                plan.id,
                {
                    "hash": digest,
                    "policy": decision.result,
                    "recommendation": recommendation["diagnosis"],
                    "recommendation_id": record.id,
                },
            )
            self.db.commit()
            return plan

    def _queue_destroy(self, principal: Principal, plan: DeploymentPlan) -> Environment:
        if plan.state not in {LifecycleState.PLANNED, LifecycleState.APPROVED}:
            raise ValueError("destroy plan is not executable")
        environment = self._environment(principal, plan.environment_id)
        self.db.add(
            ExecutionJob(
                deployment_plan_id=plan.id,
                environment_id=environment.id,
                state="QUEUED",
                result={"operation": "DESTROY"},
            )
        )
        self.audit(
            principal,
            "execution.queued",
            "environment",
            environment.id,
            {"plan_hash": plan.plan_hash},
        )
        self.db.commit()
        return environment

    def _queue_change(self, principal: Principal, plan: DeploymentPlan) -> Environment:
        if plan.state not in {LifecycleState.PLANNED, LifecycleState.APPROVED}:
            raise ValueError("change plan is not executable")
        environment = self._environment(principal, plan.environment_id)
        if LifecycleState(environment.state) not in {LifecycleState.CHANGE_PROPOSED}:
            raise ValueError("environment cannot receive a change in its current state")
        if plan.state == LifecycleState.APPROVED and not self.db.scalar(
            select(Approval).where(
                Approval.deployment_plan_id == plan.id, Approval.plan_hash == plan.plan_hash
            )
        ):
            raise ValueError("approved plan has no matching durable approval")
        require_transition(LifecycleState(environment.state), LifecycleState.QUEUED)
        environment.state = LifecycleState.QUEUED
        self.db.add(
            ExecutionJob(
                deployment_plan_id=plan.id,
                environment_id=environment.id,
                state="QUEUED",
                result={"operation": "CHANGE"},
            )
        )
        self.audit(
            principal,
            "change.execution_queued",
            "environment",
            environment.id,
            {"plan_hash": plan.plan_hash},
        )
        self.db.commit()
        return environment

    def incidents(self, principal: Principal, environment_id: str) -> list[Incident]:
        environment = self._environment(principal, environment_id)
        return list(
            self.db.scalars(
                select(Incident)
                .where(Incident.environment_id == environment.id)
                .order_by(Incident.created_at.desc())
            )
        )

    def _open_incident(self, environment: Environment, summary: str, evidence: dict) -> Incident:
        incident = self.db.scalar(
            select(Incident).where(
                Incident.environment_id == environment.id, Incident.state == "OPEN"
            )
        )
        if incident:
            return incident
        incident = Incident(
            organization_id=environment.organization_id,
            environment_id=environment.id,
            summary=summary,
            evidence=evidence,
        )
        self.db.add(incident)
        return incident

    def _recommendation_record(self, principal: Principal, environment: Environment) -> Recommendation:
        incident = self.db.scalar(
            select(Incident)
            .where(Incident.environment_id == environment.id, Incident.state == "OPEN")
            .order_by(Incident.created_at.desc())
        )
        if not incident:
            incident = self._open_incident(
                environment,
                "Latency and saturation need a bounded diagnostic recommendation.",
                self.day2_advisor.recommend(environment).evidence.model_dump(mode="json"),
            )
            self.db.flush()
        record = self.db.scalar(
            select(Recommendation)
            .where(
                Recommendation.environment_id == environment.id,
                Recommendation.incident_id == incident.id,
                Recommendation.state.in_(["PROPOSED", "PLANNED"]),
            )
            .order_by(Recommendation.created_at.desc())
        )
        if record:
            return record
        recommendation = self.day2_advisor.recommend(environment)
        record = Recommendation(
            organization_id=principal.organization_id,
            environment_id=environment.id,
            incident_id=incident.id,
            recommendation=recommendation.model_dump(mode="json"),
        )
        self.db.add(record)
        self.db.flush()
        self.audit(
            principal,
            "recommendation.created",
            "recommendation",
            record.id,
            {"environment_id": environment.id, "incident_id": incident.id},
        )
        self.db.commit()
        return record

    @staticmethod
    def _recommendation_response(record: Recommendation) -> dict[str, Any]:
        return {
            **record.recommendation,
            "record_id": record.id,
            "incident_id": record.incident_id,
            "record_state": record.state,
        }

    def _resolve_day2_records(self, plan: DeploymentPlan, environment: Environment) -> None:
        record_id = plan.payload.get("recommendation_record_id")
        if not record_id:
            return
        record = self.db.get(Recommendation, record_id)
        if record and record.organization_id == environment.organization_id:
            record.state = "APPLIED"
            if record.incident_id:
                incident = self.db.get(Incident, record.incident_id)
                if incident:
                    incident.state = "RESOLVED"

    def _environment(self, principal: Principal, environment_id: str) -> Environment:
        environment = self.db.get(Environment, environment_id)
        if not environment or environment.organization_id != principal.organization_id:
            raise PermissionError("environment not found in this organization")
        return environment

    def get_environment(self, principal: Principal, environment_id: str) -> Environment:
        return self._environment(principal, environment_id)

    def environment_payload(self, principal: Principal, environment_id: str) -> dict[str, Any]:
        environment = self._environment(principal, environment_id)
        return self._environment_payload(environment)

    def environment_payloads(self, principal: Principal) -> list[dict[str, Any]]:
        return [
            self._environment_payload(environment)
            for environment in self.db.scalars(
                select(Environment)
                .where(Environment.organization_id == principal.organization_id)
                .order_by(Environment.created_at)
            )
        ]

    def _environment_payload(self, environment: Environment) -> dict[str, Any]:
        return {
            "id": environment.id,
            "name": environment.name,
            "type": environment.environment_type,
            "state": environment.state,
            "execution_mode": environment.desired_state.get("execution_mode"),
            "customer_plan_revision_id": environment.desired_state.get(
                "customer_plan_revision_id"
            ),
            "cost_estimate": environment.desired_state.get("cost_estimate"),
            "desired_state": environment.desired_state,
            "observed_state": environment.observed_state,
            "outputs": self._environment_outputs(environment.id),
            "resources": self._observed_resources(environment.id),
        }

    def audits(self, principal: Principal, environment_id: str | None = None) -> list[AuditEvent]:
        statement = select(AuditEvent).where(
            AuditEvent.organization_id == principal.organization_id
        )
        if environment_id:
            self._environment(principal, environment_id)
            statement = statement.where(
                AuditEvent.entity_type == "environment", AuditEvent.entity_id == environment_id
            )
        return list(self.db.scalars(statement.order_by(AuditEvent.created_at)))

    def audit_evidence(
        self, principal: Principal, entity_id: str | None = None
    ) -> list[dict[str, Any]]:
        statement = select(AuditEvent).where(
            AuditEvent.organization_id == principal.organization_id
        )
        if entity_id:
            statement = statement.where(AuditEvent.entity_id == entity_id)
        events = self.db.scalars(statement.order_by(AuditEvent.created_at)).all()
        users = {
            user.subject: user.role
            for user in self.db.scalars(
                select(ProductUser).where(ProductUser.organization_id == principal.organization_id)
            )
        }
        return [self._audit_evidence_item(event, users) for event in events]

    @staticmethod
    def _audit_evidence_item(event: AuditEvent, roles: dict[str, str]) -> dict[str, Any]:
        detail = event.detail or {}
        labels = {
            "project.created": "Project created",
            "repository.analyzed": "Repository analyzed",
            "cloud_connection.created": "AWS connection metadata created",
            "intent.interpreted": "Intent interpreted",
            "deployment_plan.created": "Deployment plan created",
            "infrastructure_plan.draft_created": "Customer plan draft created",
            "infrastructure_plan.constraints_updated": "Draft constraints updated",
            "infrastructure_plan.submitted": "Plan submitted for approval",
            "infrastructure_plan.approved": "Plan approved",
            "infrastructure_plan.rejected": "Plan rejected",
            "infrastructure_plan.revised": "Plan revised",
            "customer_plan.local_dry_run_plan_created": "Local dry-run plan created",
            "customer_plan.local_dry_run_queued": "Local dry-run queued",
            "customer_plan.local_destroy_requested": "Local destroy requested",
            "environment.observed": "Environment observed",
            "environment.degraded": "Environment degraded",
            "environment.destroyed": "Environment destroyed",
        }
        return {
            "id": event.id,
            "label": labels.get(event.action, event.action.replace("_", " ").replace(".", " / ")),
            "action": event.action,
            "actor_subject": event.actor_subject,
            "actor_role": roles.get(event.actor_subject, "system"),
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "plan_digest": detail.get("digest") or detail.get("hash") or detail.get("plan_hash"),
            "revision": detail.get("revision"),
            "decision_reason": detail.get("reason"),
            "integration": detail.get("provider") or detail.get("execution"),
            "detail": detail,
            "at": event.created_at.isoformat() if event.created_at else None,
            "export_ready": True,
        }
