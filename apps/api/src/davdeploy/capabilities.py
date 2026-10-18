"""Provider-neutral capability interfaces used by planning and execution."""

from __future__ import annotations

from typing import Any, Protocol

from davdeploy.contracts import ExecutionContext, ExecutionOutcome, ProviderCapability


class ComputeProvider(Protocol):
    def discover(self, scope: dict[str, str]) -> tuple[ProviderCapability, ...]: ...


class DatabaseProvider(ComputeProvider, Protocol): ...
class StorageProvider(ComputeProvider, Protocol): ...
class NetworkingProvider(ComputeProvider, Protocol): ...
class SecretsProvider(ComputeProvider, Protocol): ...
class ObservabilityProvider(ComputeProvider, Protocol): ...


class ExecutionProvider(Protocol):
    def execute(self, context: ExecutionContext) -> ExecutionOutcome: ...


class ObservationProvider(Protocol):
    def observe(self, context: ExecutionContext) -> ExecutionOutcome: ...


class DestroyProvider(Protocol):
    def destroy(self, context: ExecutionContext) -> ExecutionOutcome: ...


class PricingProvider(Protocol):
    def estimate(self, capability: ProviderCapability, region: str) -> dict[str, Any]: ...

