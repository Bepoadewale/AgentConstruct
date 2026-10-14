# PR tickets

This directory stores one ticket file per pull request.

Use this naming rule:

```text
docs/tickets/ticket1.md
docs/tickets/ticket2.md
docs/tickets/ticket3.md
...
```

For every new PR:

1. Find the highest existing `ticketN.md`.
2. Create the next numbered ticket before implementation work starts.
3. Do not overwrite or renumber older tickets.
4. Keep the ticket updated as the PR changes.
5. Before marking the PR ready, update the acceptance-criteria checklist with met/not met evidence.

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
