# Competitive analysis

**Research date:** 2026-10-14. Claims below are based on official product documentation where linked; feature availability and pricing should be rechecked before commercial commitments.

## Competitor map

| Product/category | Verified capability | Overlap | AgentConstruct opportunity |
|---|---|---|---|
| Amazon Q Developer | AWS describes Q Developer as an AWS assistant for understanding, building, operating, reviewing code, generating IaC, querying account resources/billing, and diagnosing issues. [Official docs](https://aws.amazon.com/documentation-overview/q-developer/) | AWS-native guidance and operational assistance | Remain cloud-account/product neutral at the control-plane boundary, keep exact plan/approval/audit state, and serve teams that want a durable decision record rather than an AWS chat surface. Do not claim superior AWS knowledge without evidence. |
| AWS Well-Architected Tool/Agent | AWS documents six pillars and a Well-Architected Agent for recommendations tailored to an environment. [Official docs](https://docs.aws.amazon.com/wellarchitected/) | Architecture review, reliability, security, cost | Turn a user outcome into a deployable bounded plan, connect repository facts, preserve revisions/approval, and explain the minimum viable architecture. |
| Pulumi/Pulumi Neo | Pulumi documents AI-driven infrastructure, MCP/agent skills, previews, policy, PR review, and an agent for infrastructure analysis/maintenance. [Pulumi AI](https://www.pulumi.com/docs/ai/), [Neo](https://www.pulumi.com/docs/pulumi-cloud/neo/) | AI infrastructure planning and governed execution | Do not compete on IaC runtime breadth. Differentiate with AWS-first architecture selection, cross-tool/provider-neutral plan semantics, customer context, and an outcome-first UX. |
| Terraform/HCP Terraform MCP | HashiCorp’s MCP server provides current registry/provider/module/policy context and HCP Terraform workspace operations. [Official docs](https://developer.hashicorp.com/terraform/mcp-server) | Better AI-generated Terraform and current provider data | Treat Terraform as one execution backend; add architecture selection, cost/complexity reasoning, plan immutability and approval above it. |
| Claude Code | Anthropic documents a terminal coding agent with CLI and MCP configuration. [Official CLI docs](https://docs.anthropic.com/en/docs/claude-code/cli-usage) | Can inspect repos, run tools, and generate infrastructure code | AgentConstruct can be an MCP/API system of record and authorization boundary for Claude, rather than trying to replace it. |
| OpenAI Codex | OpenAI documents Codex as a coding agent that can read/modify/run code; the Agents API supports tools, MCP, sandboxes and durable sessions. [Codex](https://developers.openai.com/learn/codex), [Agents](https://developers.openai.com/api/docs/guides/agents) | Can generate and execute infrastructure code in a sandbox/tool loop | Provide persistent customer inventory, approved plans, cloud identity boundaries, policy, audit, observed state, and safe execution tools. |
| GitHub Copilot agent mode | GitHub documents agent mode as an autonomous coding workflow in an IDE. [Official docs](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-agent-mode) | Repository-aware implementation and tool use | Integrate as a client; do not compete for the coding surface. |

## Why use AgentConstruct instead of asking Claude Code/Codex to deploy Terraform?

Only if AgentConstruct provides durable capabilities those agents do not own by default:

1. A customer-specific inventory and ownership model across projects and accounts.
2. A typed workload and architecture history, with immutable digests and revision comparison.
3. Deterministic service/cost/security/complexity checks that reject unsafe or impossible plans.
4. Workspace-scoped approval and audit independent of the model or browser.
5. Short-lived BYOC credentials and bounded execution adapters.
6. Independent observation of the resulting state and destroy evidence.
7. A vendor-neutral plan contract that can target Terraform, GitOps, or another backend.

If AgentConstruct only produces Terraform text, the differentiation is weak and the product should not be pursued in that form.

## Research limits

This review used official documentation, not pricing pages, private customer data, or hands-on feature trials. Competitive pricing, quotas, roadmap claims, and exact enterprise controls require direct validation before sales positioning.

