# Governed AI Platform — Product Strategy

Private working repository for the future flagship product that will follow the ten public AI Infrastructure / Platform Engineering projects.

## The product thesis

Build a vendor-neutral control plane that helps enterprises operate shared AI workloads safely across tenants, models, agents, Kubernetes infrastructure, and eventually edge devices.

The product is **not** a replacement for AWS, Azure, Google Cloud, Claude Enterprise, or GitHub Copilot Enterprise. It governs the operational layer around AI products: who can use what, under which policy, at what cost, with what evidence, and how changes are rolled back.

## Executive description

> A control centre for enterprise AI that enables teams and agents to use AI safely, reliably, and cost-effectively without granting unrestricted infrastructure authority.

## Current status

This is a strategy and product-planning repository. It contains no customer data, production credentials, or commercial product implementation. The flagship should begin only after the ten focused public repositories are complete and their reusable patterns have been validated independently.

See [project status](PROJECT_STATUS.md), [implementation status](docs/IMPLEMENTATION_STATUS.md),
and [validation scope](docs/VALIDATION.md). This repository is not evidence that the
commercial product or public flagship has been implemented.

## Documents

- [Product vision](docs/product-vision.md)
- [Ideal customer and use cases](docs/ideal-customer.md)
- [Product wedge and roadmap](docs/product-roadmap.md)
- [Open-core and commercial boundaries](docs/open-core.md)
- [Go-to-market plan](docs/go-to-market.md)
- [Career and category-leadership plan](docs/category-leadership.md)
- [Portfolio-to-flagship architecture](docs/portfolio-integration.md)
- [Flagship evolution plan](docs/flagship-evolution-plan.md)
- [Decision log](docs/decision-log.md)

## Engineering principles

- Earn claims with executed evidence.
- Keep customer workloads, secrets, policies, and operational data private.
- Use public repositories for reference implementations and local-first learning.
- Productize one painful workflow before assembling a broad suite.
- Do not imitate cloud-provider breadth; provide a portable governance and operations layer above it.
