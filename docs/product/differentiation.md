# Why AgentConstruct exists

General AI tools can write infrastructure code. AgentConstruct is the governed system that remembers a customer's approved cloud context and turns an outcome into a reviewable change.

It keeps the organisation boundary, cloud connection, policies, plans, approvals, observed results, audit history, cost assumptions and recommendations. A developer can use the web UI, CLI, Codex, Claude, Cursor or another agent as a client. The client does not become the authority.

The key rule is simple:

> AI proposes. Typed policy, an approved immutable plan, and a bounded executor authorize and act.

The product does not position itself as “an LLM that writes Terraform.” It chooses the simplest viable architecture, explains why, and records what actually happened after a governed request.

**Executed locally:** the same REST API is used by the browser, CLI and MCP fixture. Plans, approvals, audit records and observed fixture results are durable.

**Not executed:** external agent installation, customer-cloud execution and live GitHub delivery.
