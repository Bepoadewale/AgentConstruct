# Evidence-backed planning

The planner may use deterministic rules, but its explanation must identify the evidence boundary. `PlanningEvidence` groups repository, inventory, capability and pricing references. `ArchitecturePlan.evidence_refs` and `evidence_limitations` expose those references and limitations to callers.

`FixturePricingCatalog` is deliberately small and explicit. It records a catalog version, capture time, assumptions and `actual_billing=false`. A future AWS pricing adapter may refresh the catalog, but must preserve the same contract and never label an estimate as settled billing.

The current planner remains backward-compatible: when no evidence bundle is supplied, the result is still valid for local demos but explicitly says that fixture inventory/pricing assumptions were used. Missing quotas, regional availability, live billing, or observed workload telemetry must remain visible limitations.

