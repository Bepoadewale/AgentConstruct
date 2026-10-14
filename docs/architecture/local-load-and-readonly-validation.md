# Local load and read-only AWS validation

`scripts/local_load_smoke.py` performs a deliberately bounded concurrent health check
against localhost. It defaults to 50 requests and five workers, rejects non-local hosts,
and fails on non-200 responses. It is a smoke signal, not a capacity claim or production
load test. Hosted load testing needs a separate environment, rate limits and an approved
test budget.

The live AWS adapter is read-only. It assumes the existing customer discovery role with
short-lived STS credentials, collects inventory and Cost Explorer evidence, and stores no
reusable credential. The adapter does not create, update or delete resources.
