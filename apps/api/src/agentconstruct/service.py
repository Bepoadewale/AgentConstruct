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
)
from agentconstruct.intent import DeterministicIntentProvider, IntentProvider
from agentconstruct.models import (
    Approval,
    AuditEvent,
    CloudConnection,
    CloudDiscoveryJob,
    DeploymentPlan,
    Environment,
    ExecutionJob,
    Incident,
    InfrastructurePlan,
    InfrastructurePlanDecisionRecord,
    InfrastructurePlanRevision,
    Organization,
    ProductUser,
    Project,
    Recommendation,
    RepositoryConnection,
    StoredArchitecturePlan,
    StoredCloudInventorySnapshot,
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
        rows = self.db.execute(
            select(InfrastructurePlanRevision, InfrastructurePlan)
            .join(InfrastructurePlan, InfrastructurePlan.id == InfrastructurePlanRevision.infrastructure_plan_id)
            .where(
                InfrastructurePlanRevision.organization_id == principal.organization_id,
                InfrastructurePlanRevision.state == InfrastructurePlanState.SUBMITTED,
            )
            .order_by(InfrastructurePlanRevision.submitted_at.desc())
        ).all()
        return [
            {
                "id": revision.id,
                "plan_id": plan.id,
                "title": plan.title,
                "revision": revision.revision_number,
                "creator_subject": plan.creator_subject,
                "content_digest": revision.content_digest,
                "submitted_at": revision.submitted_at.isoformat() if revision.submitted_at else None,
            }
            for revision, plan in rows
        ]

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
        return {
            "id": revision.id,
            "plan_id": plan.id,
            "title": plan.title,
            "creator_subject": plan.creator_subject,
            "revision": revision.revision_number,
            "state": revision.state,
            "content_digest": revision.content_digest,
            "content": revision.content,
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
        del principal
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
        }

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

    def repository_discovery(self, principal: Principal, project_id: str) -> dict[str, str]:
        project = self._project(principal, project_id)
        if not project.repository_url:
            raise ValueError("project has no repository connection")
        installation_id = getattr(self.github, "installation_id", "fixture-installation")
        metadata = self.github.inspect_repository(installation_id, project.repository_url)
        execution = getattr(self.github, "execution", "SIMULATED")
        self.audit(
            principal,
            "repository.discovered",
            "project",
            project.id,
            {"provider": metadata.provider, "repository": metadata.repository, "execution": execution},
        )
        self.db.commit()
        connection = self.db.scalar(
            select(RepositoryConnection).where(RepositoryConnection.project_id == project.id)
        )
        return metadata.__dict__ | {
            "execution": execution,
            "selected_branch": connection.selected_branch if connection else metadata.default_branch,
        }

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
        state = LifecycleState.NEEDS_INPUT if spec.unknowns else LifecycleState.PLANNED
        intent = WorkloadIntent(
            organization_id=principal.organization_id,
            project_id=project.id,
            requester_subject=principal.subject,
            prompt=prompt,
            idempotency_key=idempotency_key,
            state=state,
            spec={
                **spec.model_dump(mode="json"),
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
