"""Small authenticated REST client shared by the CLI and MCP server."""

from __future__ import annotations

from typing import Any

import httpx

API_CONTRACT_VERSION = "v1"


class ProductApiClient:
    def __init__(self, base_url: str, token: str, client: httpx.Client | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.client = client or httpx.Client(timeout=15)

    def request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        response = self.client.request(
            method,
            f"{self.base_url}{path}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": f"application/vnd.agentconstruct.{API_CONTRACT_VERSION}+json",
                "X-AgentConstruct-Client-Contract": API_CONTRACT_VERSION,
            },
            json=payload,
        )
        try:
            body = response.json()
        except ValueError:
            body = {"detail": response.text}
        if response.is_error:
            detail = (
                body.get("detail", response.reason_phrase) if isinstance(body, dict) else str(body)
            )
            raise RuntimeError(f"AgentConstruct API {response.status_code}: {detail}")
        return body
