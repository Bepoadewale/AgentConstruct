# Execution isolation and cell-ready boundaries

davdeploy is designed for many customers without giving one tenant access to
another tenant's work. `ExecutionContext` carries organization, workspace, project,
actor, plan digest, placement, timeout, network policy and an operation allowlist.

`ExecutionPlacement` gives future hosted routing a stable place to record a provider,
region and cell. A cell can later be a separately scaled worker pool or account boundary;
the product domain does not need to change when that topology evolves.

`ExecutionRunner` is the only boundary for execution. The fixture runner is local and
deterministic. It performs no shell, Terraform, Kubernetes, AWS, or secret operation.
The disabled runner fails closed. A future hosted runner must:

- verify exact approved plan digest and tenant scope;
- accept only allowlisted operations;
- use short-lived credential references, never stored credentials;
- enforce timeout and network policy;
- return observed results and safe output references;
- emit trace and audit correlation IDs;
- isolate retries and resource limits by tenant/cell.

This is a scale-ready contract, not a claim of million-customer capacity or live cloud
execution. Queue, worker, regional-cell, and provider placement remain deployment
decisions for later hosted phases.
