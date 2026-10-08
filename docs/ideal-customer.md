# Ideal customer and realistic scenarios

> **Historical strategy note.** Superseded on 2026-10-08 by [current ideal customer](product/ideal-customer.md). Preserved for history only.

## Initial ideal customer profile

A 50–2,000 person B2B software, fintech, health-tech, logistics, or regulated enterprise organisation that has:

- several teams building AI-backed features;
- shared model/API/GPU capacity;
- Kubernetes or complex cloud infrastructure;
- rising AI cost, reliability, or compliance pressure;
- a platform engineering, SRE, security, or ML platform function.

The first buyer is usually a VP Engineering, CTO, Head of Platform, Head of AI/ML, CISO-sponsored platform leader, or FinOps leader—not an individual application developer.

## Realistic 2,000-person insurance-company scenario

Twelve product teams operate claims summarisation, fraud detection, customer support, internal search, and developer-agent workflows. Each team needs AI capacity but should not receive broad cloud credentials or bypass privacy policy.

1. The claims team requests an approved document-summarisation capability.
2. The platform evaluates team identity, tenant, data classification, model approval, quota, budget, and whether a human approval is needed.
3. It creates or selects a controlled endpoint, issues scoped access, and records an auditable plan.
4. The team receives an API capability, not cluster-admin access.
5. Costs and reliability are attributed to the team, model, and workload.
6. A candidate fraud model is released gradually. If critical-slice quality or latency declines, promotion pauses and the previous version is restored.
7. A developer agent may prepare an infrastructure plan but cannot approve its own protected production request or obtain cloud-admin credentials.

## Buyer outcomes

- Faster delivery of approved AI features.
- Lower blast radius from a bad model, runaway tenant, or over-privileged agent.
- Clearer ownership, cost allocation, and audit evidence.
- Fewer manual platform-team tickets and less infrastructure toil.
