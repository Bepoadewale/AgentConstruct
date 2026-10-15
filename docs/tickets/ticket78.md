# ticket78: Prevent Terraform validation disk leaks

- PR: #78
- Branch: `fix/terraform-validation-cleanup`
- Status: complete

## Problem / goal

Local Terraform validation retained a separate provider installation for every
Terraform root under fixed `/tmp/agentconstruct-tfvalidate-*` directories. The
stale validation directories consumed 8.3 GiB, while project-local `.terraform`
directories held another 11.4 GiB of repeated provider binaries.

The goal is to keep validation reproducible while sharing downloaded providers
and guaranteeing removal of per-run Terraform data on success, failure, or an
interruption.

## Current repo state

- `make terraform-validate` initializes ten Terraform roots independently.
- Each root uses a fixed `TF_DATA_DIR` under `/tmp`.
- The Make target has no cleanup trap or shared plugin cache.
- The confirmed stale local directories were removed before this PR; source,
  state, lock, and configuration files were not touched.

## Research / references used

- Repository-local `Makefile` Terraform validation target.
- Terraform CLI `TF_DATA_DIR` and `TF_PLUGIN_CACHE_DIR` behavior.
- Local disk audit performed on 2026-10-15.

## Work planned for the PR

- Move validation orchestration into a bounded shell script.
- Allocate a unique temporary data root for each validation run.
- Clean that root through signal-safe exit traps.
- Reuse a single configurable Terraform plugin cache.
- Add regression tests for successful and failed validation cleanup.

## Acceptance criteria

- Successful validation leaves no per-run Terraform data directory.
- Failed validation leaves no per-run Terraform data directory.
- All Terraform roots still receive `init` and `validate` operations.
- Provider downloads use a shared configurable plugin cache.
- Existing lint, tests, Terraform validation, and documentation checks pass.

## Acceptance status

- [x] Successful-run cleanup is verified.
- [x] Failed-run cleanup is verified.
- [x] All configured roots remain validated.
- [x] Shared plugin caching is enabled.
- [x] Required local checks pass.

## Tests / validation performed

- `.venv/bin/python -m ruff check apps/api/src tests scripts`
- `.venv/bin/python -m pytest -q tests/test_terraform_validation.py` — 2 passed.
- `.venv/bin/python -m pytest -q` — 175 passed, 1 dependency warning.
- `.venv/bin/python scripts/check_doc_conventions.py`
- `git diff --check`
- `make terraform-validate` — all ten roots initialized and validated; subsequent
  roots reused the shared cache.
- Post-run check — zero `agentconstruct-tfvalidate*` directories remained under
  `/private/tmp`; the shared provider cache occupied 692 MiB.

## Evidence files produced

None. This changes local and CI validation behavior only; it does not execute a
customer workload or apply Terraform.

## Boundaries

- No Terraform state, lock files, source configuration, credentials, or cloud
  resources are changed.
- The shared plugin cache remains disposable and contains provider binaries only.

## Follow-up work

- Consider using the same bounded validation helper in other infrastructure
  repositories that currently retain project-local provider installations.
