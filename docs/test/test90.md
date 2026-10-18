# test90: Automatic production plan selection

Date: 2026-10-18

Execution type: Local clean-room validation, static workflow tests, and read-only GitHub Actions API
validation. No AWS plan or apply was run.

Customer repository: AgentConstruct repository and local deterministic fixtures only; no customer
repository or workload.

Commit: Implementation commit `83786b6` on branch
`feat/automatic-production-plan-selection`.

AWS account: `654654474502` remains the configured target; it was not accessed for this validation.

AWS region: `us-east-1` remains the configured target.

## Resources created

The clean-room cycle created ephemeral local Docker containers, a network, a PostgreSQL volume,
and a Python virtual environment. Final cleanup removed them. No AWS or GitHub resource was created
or modified.

## Commands executed

```text
make clean-local
make bootstrap-local
make smoke
make demo-simple
make demo-complex
make demo-degraded
make demo-day2
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make terraform-validate
make clean-local
gh api repos/Bepoadewale/AgentConstruct/actions/workflows/terraform-plan.yml/runs
```

## Observed result

- The apply dispatch form contains only `confirmation`.
- Plan run ID and run attempt are resolved from the GitHub Actions API.
- Selection is restricted to manual plan runs from `main` with the exact current commit SHA.
- The newest matching run must have a successful conclusion.
- Apply still verifies workflow name, workflow path, event, branch, run identity, manifest version,
  production marker, commit, and SHA-256 digest.
- The read-only query resolved successful historical plan `39140954204`, attempt 1, for commit
  `3f4fe983a1b34a91e42967c1057bb723c20bdad9`.
- The query returned no plan for the newer current `main` commit, so apply would fail closed.
- The complete clean-room sequence passed.
- `make verify` passed 226 tests with one upstream dependency deprecation warning.
- All Terraform roots passed initialization without backends and static validation.

## Teardown

`make clean-local` removed the local containers, network, volume, `.venv`, and `.local`. No cloud
teardown was required because no cloud resource was created.

## Final boundary

This evidence proves local product correctness, workflow contract checks, exact-commit automatic
plan selection, and fail-closed behavior for an unplanned commit. It does not prove Terraform apply,
a deployed control plane, live authentication, customer traffic, or customer workload execution.
