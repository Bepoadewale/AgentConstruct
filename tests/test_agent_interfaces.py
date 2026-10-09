from __future__ import annotations

import json
from argparse import Namespace

from agentconstruct.cli import run
from agentconstruct.mcp import TOOL_DEFINITIONS, AgentConstructMcp, handle_request
from agentconstruct.policy import PolicyClient
from agentconstruct.security import LOCAL_USERS, Principal
from agentconstruct.service import ProductService
from test_product import LocalExecutor, complete_prompt, founder, make_service


class RecordingClient:
    def __init__(self):
        self.calls: list[tuple[str, str, dict | None]] = []

    def request(self, method: str, path: str, payload: dict | None = None):
        self.calls.append((method, path, payload))
        if path.startswith("/api/v1/deployment-plans/"):
            return {
                "id": "plan-1",
                "state": "APPROVAL_REQUIRED",
                "plan_hash": "a" * 64,
                "policy_result": "APPROVAL_REQUIRED",
                "payload": {
                    "architecture": {
                        "profile": "aws-app-runner",
                        "cost_estimate": {"monthly_low": 65, "monthly_high": 180},
                        "candidates": [{"candidate_id": "aws-app-runner"}],
                    }
                },
            }
        return {"ok": True}


def test_mcp_catalogue_exposes_governed_operations_but_no_approval_or_credentials():
    names = {tool["name"] for tool in TOOL_DEFINITIONS}
    assert {
        "analyze_workload",
        "plan_infrastructure",
        "get_plan",
        "recommend_optimization",
        "create_change_plan",
        "destroy_environment",
    } <= names
    assert "approve_plan" not in names
    assert all("credential" not in name for name in names)


def test_mcp_compares_candidates_and_preserves_api_authority():
    client = RecordingClient()
    result = AgentConstructMcp(client).call_tool("compare_architectures", {"plan_id": "plan-1"})
    assert result["selected"] == "aws-app-runner"
    assert client.calls == [("GET", "/api/v1/deployment-plans/plan-1", None)]


def test_mcp_day2_tools_only_request_governed_api_operations():
    client = RecordingClient()
    server = AgentConstructMcp(client)
    assert server.call_tool("recommend_optimization", {"environment_id": "env-1"}) == {"ok": True}
    assert server.call_tool("create_change_plan", {"environment_id": "env-1"}) == {"ok": True}
    assert client.calls == [
        ("GET", "/api/v1/environments/env-1/recommendation", None),
        ("POST", "/api/v1/environments/env-1/change-plan", None),
    ]


def test_mcp_json_rpc_tools_list_and_error_shape_are_deterministic():
    server = AgentConstructMcp(RecordingClient())
    listed = handle_request(server, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert listed and listed["result"]["tools"] == TOOL_DEFINITIONS
    invalid = handle_request(
        server,
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "approve_plan"}},
    )
    assert invalid and invalid["result"]["isError"] is True
    assert "unknown MCP tool" in invalid["result"]["content"][0]["text"]
    assert json.loads(json.dumps(listed))["jsonrpc"] == "2.0"


def test_cli_forwards_analyze_request_without_creating_cloud_credentials():
    client = RecordingClient()
    result = run(
        Namespace(
            command="analyze-workload",
            project_id="project-1",
            prompt="Deploy a small AI API in AWS with a budget under $300.",
            repository="https://github.com/example/api",
            cloud_connection_id="connection-1",
            idempotency_key="agent-client-001",
        ),
        client,
    )
    assert result == {"ok": True}
    assert client.calls == [
        (
            "POST",
            "/api/v1/intents",
            {
                "project_id": "project-1",
                "prompt": "Deploy a small AI API in AWS with a budget under $300.",
                "source_repository": "https://github.com/example/api",
                "cloud_connection_id": "connection-1",
                "idempotency_key": "agent-client-001",
            },
        )
    ]


def test_agent_read_interfaces_remain_tenant_scoped():
    service, db = make_service()
    project = service.create_project(founder(), "agent-read", "https://github.com/example/agent")
    intent = service.create_intent(
        founder(), project.id, complete_prompt(), None, None, "agent-read-interface-001"
    )
    plan = service.plan_intent(founder(), intent.id)
    assert service.get_plan(founder(), plan.id).id == plan.id
    subject, organization_id, role = LOCAL_USERS["other-tenant"]
    other = Principal(subject, organization_id, role)
    try:
        service.get_plan(other, plan.id)
    except PermissionError:
        pass
    else:
        raise AssertionError("agent read crossed tenant boundary")
    restarted = ProductService(db, policy=PolicyClient(fixture=True), executor=LocalExecutor())
    assert restarted.get_plan(founder(), plan.id).plan_hash == plan.plan_hash
