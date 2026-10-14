# PR tickets

This directory stores one ticket file per pull request.

Use the GitHub PR number as the naming rule:

```text
docs/tickets/ticket42.md  # PR #42
docs/tickets/ticket43.md  # PR #43
docs/tickets/ticket44.md  # PR #44
...
```

For every new PR:

1. Open a draft PR early enough to know the PR number.
2. Create `docs/tickets/ticketN.md`, where `N` is that PR number.
3. Create the ticket before substantive implementation work starts.
4. Do not overwrite or renumber older tickets.
5. Keep the ticket updated as the PR changes.
6. Before marking the PR ready, update the acceptance-criteria checklist with met/not met evidence.

Each ticket must include:

- PR title and branch.
- Problem / goal.
- Current repo state relevant to the PR.
- Research / references used, including whether they are local code, docs, AWS/GitHub evidence, or external documentation.
- Work planned for the PR.
- Acceptance criteria.
- Acceptance status: met, partially met, or not met.
- Tests / validation performed.
- Evidence files produced, if any.
- Boundaries and follow-up work.

`docs/VALIDATION.md` may summarize executed evidence, but tickets are the source of truth for what each PR intended to change and whether its acceptance criteria were met.
