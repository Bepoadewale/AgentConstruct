# Integration Boundaries

Production integrations live behind narrow contracts in `davdeploy.integrations`. See [governed integrations](../docs/architecture/governed-integrations.md) for the evidence boundary.

- **GitHub:** a GitHub App installation, not a personal access token, will inspect repositories, validate signed webhooks, and publish a reviewed desired-state pull request with required checks.
- **AWS:** a customer-scoped IAM role will be assumed through short-lived OIDC/STS credentials. The browser, CLI, and MCP server do not receive them.
- **Slack:** a future scoped notifier can deliver approved alerts.

The local GitHub and AWS fixtures are deterministic. They cannot write to GitHub, call AWS, or return cloud credentials.
