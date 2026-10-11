# Plan Approval Architecture

The customer planning path is deliberately separate from the existing local execution-plan path.

```mermaid
sequenceDiagram
  participant Dev as Developer
  participant API as AgentConstruct API
  participant DB as PostgreSQL
  participant Admin as Workspace administrator
  Dev->>API: create draft revision
  API->>DB: store content and canonical digest
  Dev->>API: submit exact draft
  API->>DB: freeze revision as SUBMITTED and audit
  Admin->>API: approve or reject exact digest
  API->>DB: transactional decision, state and audit
```

The API verifies tenant membership and role on every operation. A customer plan decision does not grant GitHub or AWS access and does not trigger deployment.
