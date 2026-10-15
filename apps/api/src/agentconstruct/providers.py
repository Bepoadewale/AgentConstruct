"""Provider-neutral configuration seams for planned external integrations.

These settings do not initiate OAuth, send email, bill customers, or contact
AWS/Google. They make explicit what a later adapter may consume.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfiguration:
    identity: str
    email: str
    billing: str
    analytics: str
    google_workspace_domain: str | None

    @classmethod
    def from_environment(cls) -> ProviderConfiguration:
        return cls(
            identity=os.getenv("AGENTCONSTRUCT_IDENTITY_PROVIDER", "local"),
            email=os.getenv("AGENTCONSTRUCT_EMAIL_PROVIDER", "disabled"),
            billing=os.getenv("AGENTCONSTRUCT_BILLING_PROVIDER", "manual"),
            analytics=os.getenv("AGENTCONSTRUCT_ANALYTICS_PROVIDER", "local"),
            google_workspace_domain=os.getenv("AGENTCONSTRUCT_GOOGLE_WORKSPACE_DOMAIN") or None,
        )

    def validation_errors(self, *, hosted: bool) -> list[str]:
        errors: list[str] = []
        if self.identity not in {"local", "google_workspace", "cognito"}:
            errors.append("AGENTCONSTRUCT_IDENTITY_PROVIDER must be local, google_workspace, or cognito")
        if self.email not in {"disabled", "gmail_api", "ses"}:
            errors.append("AGENTCONSTRUCT_EMAIL_PROVIDER must be disabled, gmail_api, or ses")
        if self.billing not in {"manual", "stripe"}:
            errors.append("AGENTCONSTRUCT_BILLING_PROVIDER must be manual or stripe")
        if self.analytics not in {"local", "posthog"}:
            errors.append("AGENTCONSTRUCT_ANALYTICS_PROVIDER must be local or posthog")
        if self.identity == "google_workspace" and not self.google_workspace_domain:
            errors.append("Google Workspace identity requires AGENTCONSTRUCT_GOOGLE_WORKSPACE_DOMAIN")
        if hosted and self.identity == "local":
            errors.append("hosted mode requires google_workspace or cognito identity")
        return errors
