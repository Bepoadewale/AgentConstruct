"""Provider-neutral model gateway with safe fixture and disabled adapters."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from agentconstruct.contracts import (
    EvidenceKind,
    EvidenceRef,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)


class ModelGatewayUnavailable(RuntimeError):
    """Raised when no model provider is configured."""


class ModelCallPolicy(BaseModel):
    """Tenant-safe budget and timeout admission before a provider call."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_output_tokens: int = Field(default=2_000, ge=1, le=100_000)
    max_timeout_seconds: int = Field(default=60, ge=1, le=900)
    allowed_providers: frozenset[str] = frozenset({"fixture"})

    def validate(self, request: ModelRequest) -> None:
        if request.provider not in self.allowed_providers:
            raise ModelGatewayUnavailable(f"model provider {request.provider!r} is not allowed")
        if request.max_output_tokens > self.max_output_tokens:
            raise ModelGatewayUnavailable("model output budget exceeds tenant policy")
        if request.timeout_seconds > self.max_timeout_seconds:
            raise ModelGatewayUnavailable("model timeout exceeds tenant policy")


class ModelGateway(Protocol):
    def complete(self, request: ModelRequest, document: dict[str, Any]) -> ModelResponse: ...


class DisabledModelGateway:
    def complete(self, request: ModelRequest, document: dict[str, Any]) -> ModelResponse:
        del request, document
        raise ModelGatewayUnavailable("no model gateway is configured")


class DeterministicModelGateway:
    """Local fixture; it proves the contract but does not claim AI reasoning."""

    provider = "fixture"
    model = "deterministic-fixture"

    def complete(self, request: ModelRequest, document: dict[str, Any]) -> ModelResponse:
        serialized = json.dumps(document, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode()).hexdigest()
        return ModelResponse(
            request=request,
            output={
                "mode": "SIMULATED",
                "purpose": request.purpose.value,
                "input_digest": digest,
                "document_fields": sorted(document),
            },
            evidence=(
                EvidenceRef(
                    tenant=request.tenant,
                    kind=EvidenceKind.FIXTURE,
                    source="deterministic-model-fixture",
                    content_digest=digest,
                    limitations=("not a language-model response",),
                ),
            ),
            usage=ModelUsage(input_tokens=len(serialized.split()), output_tokens=8),
        )


def configured_model_gateway() -> ModelGateway:
    provider = os.getenv("AGENTCONSTRUCT_MODEL_PROVIDER", "fixture").lower()
    if provider == "disabled":
        return DisabledModelGateway()
    return DeterministicModelGateway()


def guarded_complete(
    gateway: ModelGateway,
    request: ModelRequest,
    document: dict[str, Any],
    policy: ModelCallPolicy | None = None,
) -> ModelResponse:
    """Apply model admission policy before delegating to any provider."""

    (policy or ModelCallPolicy()).validate(request)
    return gateway.complete(request, document)
