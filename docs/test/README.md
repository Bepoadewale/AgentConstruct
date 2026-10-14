# Customer workload test evidence

This directory stores one immutable evidence file per PR that performs customer workload testing.

Use the GitHub PR number as the naming rule:

```text
docs/test/test42.md  # PR #42
docs/test/test43.md  # PR #43
docs/test/test44.md  # PR #44
...
```

For every PR that performs customer workload testing:

1. Open a draft PR early enough to know the PR number.
2. Create `docs/test/testN.md`, where `N` is that PR number.
3. If the PR has multiple workload cycles, record all cycles in that same file.
4. Do not overwrite or renumber older evidence.
5. Record whether the run was local, simulated, statically validated, or real AWS execution.
6. Include the exact repository, commit, account, region, commands, resources created, observed result, teardown command, final absence check, retained resources, and limitations.

`docs/VALIDATION.md` may summarize several tests, but this directory is the source of per-PR customer workload evidence.
