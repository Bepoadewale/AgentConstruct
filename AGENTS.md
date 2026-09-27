# Agent Guide

## Mission

Maintain the private product, market and flagship strategy for the Governed AI
Operations Platform. This repository is intentionally private because it may contain
commercial positioning, buyer hypotheses, packaging decisions and acquisition strategy.

## Current scope

This is a strategy repository, not a runnable product implementation. Do not present
it as validation evidence for the public flagship or its component repositories.

## Engineering and confidentiality rules

- Never copy commercial strategy, pricing, buyer analysis, acquisition options or
  confidential notes into a public repository, issue, README, source comment or commit
  message.
- Never commit credentials, customer data, private keys or deal-specific material.
- Preserve a strict boundary: public repositories contain technical evidence; this
  repository contains private product strategy.
- Make claims traceable to validated public-repository evidence or label them as a
  hypothesis, roadmap item or decision.
- Do not begin flagship implementation here. Its public technical work belongs in
  `multi-tenant-ai-inference-platform`.
- Do not push directly to `main`; use a focused branch and PR.

## Required reading before work

Read `PROJECT_STATUS.md`, `CODEX_BACKLOG.md`, `DEFINITION_OF_DONE.md`, and the relevant
strategy document before editing.

## Completion and reproducibility

Do not mark an implementation repository `PORTFOLIO COMPLETE — LOCAL-FIRST SCOPE`
unless its own repository-specific completion gate has executed evidence. Interfaces,
documentation, mocks and static checks alone are insufficient.

If this repository later gains runnable tools, demos or generators, they must have a
documented, project-scoped clean-room bootstrap, validation and teardown path. Do not
infer reproducibility from a pre-existing developer environment.

## Before finishing

- Check links and document consistency.
- Run the relevant lightweight validation if configured.
- Update `PROJECT_STATUS.md`, `CODEX_BACKLOG.md` and `docs/VALIDATION.md` truthfully.
- Commit a focused conventional-style change and push it to the current branch.
