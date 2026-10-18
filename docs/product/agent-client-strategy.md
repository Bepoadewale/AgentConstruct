# Agent Client Strategy

General AI tools can reason about infrastructure. davdeploy keeps the durable customer context and the safety controls that those tools should not own.

```text
human web UI, CLI, Codex, Claude, Cursor, or another agent
  → davdeploy REST API or MCP server
  → typed request, policy, immutable plan, independent approval
  → bounded executor and observed result
```

The product stores the organisation boundary, projects, approved cloud target, plans, approvals, observed state, and audit history. A general AI client can ask it to analyse, compare, plan, inspect, diagnose, or propose. It cannot use davdeploy to self-approve a protected change, obtain cloud credentials, run arbitrary Terraform, run `kubectl`, or read unrestricted secrets.

## Local V1 interfaces

- **REST API:** the web UI and other clients use the same authenticated API.
- **CLI:** `davdeploy` forwards the caller's bearer token to that API. It can create/read/submit customer-plan reviews, list administrator review queues when the caller is authorized, and request approved local dry-run execution.
- **MCP:** `davdeploy-mcp` is a stdio server that exposes safe planning, customer-plan review creation/read/submission, bounded approved dry-run request, Day-2 recommendation/change-plan request, environment inspection, and destroy-plan tools.

The CLI and MCP server do not mint AWS credentials. Their token is only for the davdeploy API. The API remains the authority for tenant checks, policy, exact-plan approval, and execution state. MCP intentionally has no approval tool, so an agent cannot approve its own protected plan.

The same API exposes tenant-scoped repository and cloud-connection surfaces. Fixture mode is fully local. The live GitHub adapter can read authorized repository metadata with a short-lived installation token and refuses writes. The live AWS discovery pilot proved short-lived STS role chaining for read-only inventory and cost discovery, while storing no reusable customer credential. Neither path publishes a pull request, returns credentials to the caller, or deploys infrastructure. See [governed integrations](../architecture/governed-integrations.md).

**Executed locally:** MCP request dispatch and CLI request construction are unit tested, including customer-plan review creation/read/submission and approved dry-run request forwarding. The REST workflow, including the approved Day-2 fixture change and customer-plan review lifecycle, remains covered by the Compose demos.

**Not executed:** an external Codex, Claude, Cursor, live GitHub write/check integration, or customer-cloud execution. Those clients can be connected later using the documented stdio/API boundary.
