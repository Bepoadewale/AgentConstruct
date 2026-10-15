import httpx
from agentconstruct.client import API_CONTRACT_VERSION, ProductApiClient
from agentconstruct.mcp import MCP_TOOL_SCHEMA_VERSION, AgentConstructMcp, handle_request
from agentconstruct.policy import AuthorizationRequest, FailClosedAuthorizationService


def test_authorization_boundary_requires_approval_for_privileged_operations():
    service = FailClosedAuthorizationService()
    request = AuthorizationRequest(actor_id="user", tenant_id="org", operation="apply", plan_digest="a" * 64, scope="project")
    assert service.authorize(request).result.value == "APPROVAL_REQUIRED"
    approved = request.__class__(**{**request.__dict__, "approval": "approval-1"})
    assert service.authorize(approved).result.value == "ALLOW"


def test_client_and_mcp_expose_stable_versions():
    assert API_CONTRACT_VERSION == "v1"
    assert MCP_TOOL_SCHEMA_VERSION == "v1"
    response = handle_request(AgentConstructMcp.__new__(AgentConstructMcp), {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response["result"]["schemaVersion"] == MCP_TOOL_SCHEMA_VERSION


def test_rest_client_advertises_contract_version():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.headers)
        return httpx.Response(200, json={"ok": True})

    client = ProductApiClient("http://test", "token", httpx.Client(transport=httpx.MockTransport(handler)))
    assert client.request("GET", "/api/v1/me")["ok"] is True
    assert seen["x-agentconstruct-client-contract"] == "v1"
