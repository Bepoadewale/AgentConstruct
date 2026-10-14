"""Provider-neutral model gateway with safe fixture and disabled adapters."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Protocol

from agentconstruct.contracts import (
    EvidenceKind,
    EvidenceRef,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)


class ModelGatewayUnavailable(RuntimeError):
    """Raised when no model provider is configured."""


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

