"""Client contract compatibility and deprecation metadata."""

from __future__ import annotations

from dataclasses import dataclass

API_CONTRACT_VERSION = "v1"


@dataclass(frozen=True)
class ContractRelease:
    version: str
    status: str = "current"
    sunset: str | None = None
    replacement: str | None = None


RELEASES = (ContractRelease(API_CONTRACT_VERSION),)


def compatibility_headers(version: str = API_CONTRACT_VERSION) -> dict[str, str]:
    release = next((item for item in RELEASES if item.version == version), None)
    if release is None:
        raise ValueError(f"unsupported contract version: {version}")
    headers = {"X-AgentConstruct-API-Version": release.version}
    if release.status != "current":
        headers["Deprecation"] = "true"
        if release.sunset:
            headers["Sunset"] = release.sunset
        if release.replacement:
            headers["Link"] = f"<{release.replacement}>; rel=successor-version"
    return headers
