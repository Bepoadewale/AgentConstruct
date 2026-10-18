# Provider-neutral architecture, single-cloud default

davdeploy separates workload capabilities from provider resources. The first implemented planner catalogue is AWS-only, but its provider boundary makes future adapters possible.

One provider is the normal recommendation. Multi-cloud adds network paths, identity rules, data-transfer cost, duplicate recovery work and harder observation. The planner should recommend it only when a real requirement—such as residency, resilience policy or an unavailable capability—outweighs that cost and complexity.

The current planner has a test that rejects an unnecessary multi-cloud option even when its raw estimate is slightly lower, because the single-cloud option is simpler and remains within the cheapest viable cost band.

**Executed locally:** provider-neutral planning and the AWS fixture catalogue.

**Roadmap:** live AWS discovery and pricing, then separately validated Azure, GCP, OCI, DigitalOcean and Huawei adapters. No provider other than AWS has execution support or cloud evidence.
