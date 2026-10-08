# Integration Boundaries

Production integrations live behind narrow contracts in `agentconstruct.integrations`.

- **GitHub:** a GitHub App installation, not a personal access token, will inspect repositories and publish reviewed desired state.
- **AWS:** a customer-scoped role will be assumed through short-lived STS credentials. Local V1 has no AWS credentials or AWS calls.
- **Slack:** a future scoped notifier can deliver approved alerts.

The local GitHub fixture is deterministic and cannot write to GitHub.
