# Definition of Done

## Strategy-change acceptance criteria

- [ ] The change has a clear decision, hypothesis or evidence purpose.
- [ ] Confidential commercial material remains in this private repository.
- [ ] Public technical claims link to executed evidence or are explicitly labeled as
  roadmap/hypothesis.
- [ ] The relevant documents and decision log are consistent.
- [ ] `PROJECT_STATUS.md` and `CODEX_BACKLOG.md` remain factual.
- [ ] The change is reviewed through a PR and does not claim a runnable product without evidence.

# Portfolio Complete — Local-First Scope Gate

This repository is not the product implementation and cannot itself reach
`PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE` while it remains strategy-only. That maturity
belongs to the public flagship repository and requires its repository-specific gate:

- [ ] Real local runtime and important integrations.
- [ ] Durable/recoverable state where relevant.
- [ ] Executed security boundary, success path, failure path and rollback/recovery.
- [ ] Appropriate observability, meaningful tests and green CI.
- [ ] Safe clean-room bootstrap, demo, validation, teardown and second bootstrap.
- [ ] Truthful documentation distinguishing executed, simulated and unexecuted work.

# Clean-Room Reproducibility Gate

Not applicable while this repository has no runtime. If code, a generator or a local
service is added, it cannot be treated as complete until:

- [ ] Bootstrap dependencies from project-scoped clean state.
- [ ] Run a documented success and failure/security scenario.
- [ ] Run full validation.
- [ ] Safely remove only project-owned resources.
- [ ] Confirm a second bootstrap succeeds.
- [ ] Record real evidence in `docs/VALIDATION.md`.
