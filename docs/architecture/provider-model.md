# Provider Model

AgentConstruct plans in capabilities first and maps them to a cloud provider second. The current executable catalogue is AWS-only. Other clouds are future adapters, not supported execution targets.

The provider boundary covers:

- identity and short-lived access;
- inventory discovery and approved regions;
- compute, serverless, containers, Kubernetes, and accelerators;
- databases, storage, queues, secrets, networking, and load balancing;
- pricing, execution, observation, and destroy.

The local `CloudDiscovery` interface is deliberately narrow. Its AWS fixture returns approved regions and reusable-resource names without credentials or network access. A future AWS adapter must assume a customer-scoped role with short-lived credentials. Azure, GCP, OCI, DigitalOcean, and Huawei adapters are roadmap-only.

Single-provider designs are the default. Multi-cloud is a future capability only when a real requirement outweighs extra networking, identity, egress, observability, and recovery complexity.
