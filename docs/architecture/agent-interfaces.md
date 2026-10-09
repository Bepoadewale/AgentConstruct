# Agent Interfaces

AgentConstruct has one governed product API. The browser, CLI, and MCP server use it instead of carrying separate infrastructure authority.

| Interface | Local capability | Safety boundary |
| --- | --- | --- |
| REST | Create intent, plan, inspect plan/environment/audit, execute an eligible plan, and create a destroy plan | Bearer identity, tenant checks, policy, immutable plans and approval stay server-side |
| CLI | A thin authenticated REST client | It does not fetch cloud credentials or bypass API checks |
| MCP | Stdio tools for analysis, planning, comparison, cost, plan/status/audit reads, eligible execution, and destroy-plan creation | It has no approval tool and no shell, Terraform, kubectl, cloud-admin or secret tool |

The MCP `execute_approved_plan` name is deliberate: it forwards a request to the API, which rejects denied, stale, and unapproved protected plans. The MCP process never decides that a plan is approved.

## Local use

Start the local stack, obtain a local fixture API token, then set it only in your shell:

```bash
export AGENTCONSTRUCT_API_URL=http://127.0.0.1:8080
export AGENTCONSTRUCT_TOKEN="$(curl -fsS -X POST "$AGENTCONSTRUCT_API_URL/api/v1/auth/local-login" -H 'content-type: application/json' -d '{"username":"founder"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"
agentconstruct --help
agentconstruct-mcp
```

The local token is a development fixture. Do not use it as a production identity design and do not commit it.
