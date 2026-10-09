"""A small stdio MCP server exposing only governed AgentConstruct operations."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from agentconstruct.client import ProductApiClient

TOOL_DEFINITIONS = [
    {
        "name": "analyze_workload",
        "description": "Turn a workload outcome into a typed request. It does not execute infrastructure.",
        "inputSchema": {
            "type": "object",
            "required": ["project_id", "prompt", "idempotency_key"],
            "properties": {
                "project_id": {"type": "string"},
                "prompt": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "source_repository": {"type": "string"},
                "cloud_connection_id": {"type": "string"},
            },
        },
    },
    {
        "name": "plan_infrastructure",
        "description": "Create a policy-evaluated immutable plan from an interpreted workload.",
        "inputSchema": {
            "type": "object",
            "required": ["intent_id"],
            "properties": {"intent_id": {"type": "string"}},
        },
    },
    {
        "name": "compare_architectures",
        "description": "Return the selected architecture and alternatives from an existing immutable plan.",
        "inputSchema": {
            "type": "object",
            "required": ["plan_id"],
            "properties": {"plan_id": {"type": "string"}},
        },
    },
    {
        "name": "get_cost_estimate",
        "description": "Return the fixture cost estimate and assumptions from an existing plan. It is not actual AWS billing.",
        "inputSchema": {
            "type": "object",
            "required": ["plan_id"],
            "properties": {"plan_id": {"type": "string"}},
        },
    },
    {
        "name": "get_plan",
        "description": "Read a tenant-scoped immutable deployment plan.",
        "inputSchema": {
            "type": "object",
            "required": ["plan_id"],
            "properties": {"plan_id": {"type": "string"}},
        },
    },
    {
        "name": "get_approval_status",
        "description": "Read plan state and approval requirement. This server has no approval tool.",
        "inputSchema": {
            "type": "object",
            "required": ["plan_id"],
            "properties": {"plan_id": {"type": "string"}},
        },
    },
    {
        "name": "execute_approved_plan",
        "description": "Ask the governed API to execute an already executable plan. API policy and exact-plan approval remain authoritative.",
        "inputSchema": {
            "type": "object",
            "required": ["plan_id"],
            "properties": {"plan_id": {"type": "string"}},
        },
    },
    {
        "name": "get_environment_status",
        "description": "Read independently observed environment state.",
        "inputSchema": {
            "type": "object",
            "required": ["environment_id"],
            "properties": {"environment_id": {"type": "string"}},
        },
    },
    {
        "name": "explain_environment",
        "description": "Read the tenant-scoped desired and independently observed state for an environment.",
        "inputSchema": {
            "type": "object",
            "required": ["environment_id"],
            "properties": {"environment_id": {"type": "string"}},
        },
    },
    {
        "name": "recommend_optimization",
        "description": "Return a non-mutating Day-2 recommendation from bounded local telemetry evidence.",
        "inputSchema": {
            "type": "object",
            "required": ["environment_id"],
            "properties": {"environment_id": {"type": "string"}},
        },
    },
    {
        "name": "create_change_plan",
        "description": "Create a governed immutable change plan. It does not approve or autonomously apply a protected change.",
        "inputSchema": {
            "type": "object",
            "required": ["environment_id"],
            "properties": {"environment_id": {"type": "string"}},
        },
    },
    {
        "name": "get_audit_events",
        "description": "Read tenant-scoped audit events, optionally for one environment.",
        "inputSchema": {"type": "object", "properties": {"environment_id": {"type": "string"}}},
    },
    {
        "name": "destroy_environment",
        "description": "Create a governed destroy plan. It does not approve or execute protected deletion.",
        "inputSchema": {
            "type": "object",
            "required": ["environment_id"],
            "properties": {"environment_id": {"type": "string"}},
        },
    },
]


class AgentConstructMcp:
    def __init__(self, client: ProductApiClient):
        self.client = client

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name == "analyze_workload":
            return self.client.request("POST", "/api/v1/intents", arguments)
        if name == "plan_infrastructure":
            return self.client.request("POST", f"/api/v1/intents/{arguments['intent_id']}/plans")
        if name in {
            "compare_architectures",
            "get_cost_estimate",
            "get_plan",
            "get_approval_status",
        }:
            plan = self.client.request("GET", f"/api/v1/deployment-plans/{arguments['plan_id']}")
            if name == "compare_architectures":
                return {
                    "selected": plan["payload"]["architecture"]["profile"],
                    "candidates": plan["payload"]["architecture"]["candidates"],
                }
            if name == "get_cost_estimate":
                return plan["payload"]["architecture"]["cost_estimate"]
            if name == "get_approval_status":
                return {key: plan[key] for key in ("id", "state", "plan_hash", "policy_result")}
            return plan
        if name == "execute_approved_plan":
            return self.client.request(
                "POST", f"/api/v1/deployment-plans/{arguments['plan_id']}/execute"
            )
        if name in {"get_environment_status", "explain_environment"}:
            return self.client.request("GET", f"/api/v1/environments/{arguments['environment_id']}")
        if name == "recommend_optimization":
            return self.client.request(
                "GET", f"/api/v1/environments/{arguments['environment_id']}/recommendation"
            )
        if name == "create_change_plan":
            return self.client.request(
                "POST", f"/api/v1/environments/{arguments['environment_id']}/change-plan"
            )
        if name == "get_audit_events":
            suffix = (
                f"?environment_id={arguments['environment_id']}"
                if arguments.get("environment_id")
                else ""
            )
            return self.client.request("GET", f"/api/v1/audit-events{suffix}")
        if name == "destroy_environment":
            return self.client.request(
                "POST", f"/api/v1/environments/{arguments['environment_id']}/destroy-plan"
            )
        raise ValueError(f"unknown MCP tool: {name}")


def handle_request(server: AgentConstructMcp, request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        result = {
            "protocolVersion": request.get("params", {}).get("protocolVersion", "2025-03-26"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "agentconstruct", "version": "0.1.0"},
        }
    elif method == "tools/list":
        result = {"tools": TOOL_DEFINITIONS}
    elif method == "tools/call":
        params = request.get("params", {})
        try:
            payload = server.call_tool(params["name"], params.get("arguments", {}))
            result = {"content": [{"type": "text", "text": json.dumps(payload, default=str)}]}
        except (KeyError, ValueError, RuntimeError) as error:
            result = {"content": [{"type": "text", "text": str(error)}], "isError": True}
    else:
        if request_id is None:
            return None
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": "method not found"},
        }
    if request_id is None:
        return None
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main() -> int:
    token = os.getenv("AGENTCONSTRUCT_TOKEN")
    if not token:
        print(
            "AGENTCONSTRUCT_TOKEN is required; MCP never obtains cloud credentials", file=sys.stderr
        )
        return 2
    server = AgentConstructMcp(
        ProductApiClient(os.getenv("AGENTCONSTRUCT_API_URL", "http://127.0.0.1:8080"), token)
    )
    for line in sys.stdin:
        if not line.strip():
            continue
        response = handle_request(server, json.loads(line))
        if response is not None:
            print(json.dumps(response), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
