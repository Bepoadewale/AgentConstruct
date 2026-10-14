# Customer workload test evidence

This directory stores one immutable evidence file per customer workload test run.

Use this naming rule:

```text
docs/test/test1.md
docs/test/test2.md
docs/test/test3.md
...
```

For every new customer workload run:

1. Find the highest existing `testN.md`.
2. Create the next numbered file.
3. Do not overwrite or renumber older evidence.
4. Record whether the run was local, simulated, statically validated, or real AWS execution.
5. Include the exact repository, commit, account, region, commands, resources created, observed result, teardown command, final absence check, retained resources, and limitations.

`docs/VALIDATION.md` may summarize several tests, but this directory is the source of per-run customer workload evidence.
