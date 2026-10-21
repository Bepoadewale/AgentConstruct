# test117

Date: 2026-10-21
Execution type: Real authenticated production discovery followed by focused local regression tests
Customer repository: `https://github.com/Bepoadewale/ai-platform-control-plane`
Commit: Pending
AWS account: Existing DavDeploy control-plane account
AWS region: `us-east-1`

## Resources created

One production project, two intents, one viable architecture plan, one draft customer review, and
one cancelled invitation record were created as durable control-plane evidence. No customer cloud
resources were created.

## Commands executed

Pending focused regression commands.

## Observed result

Authentication, invitation listing, public GitHub discovery, Nova 2 Lite intent interpretation,
governed planning, and draft customer review creation succeeded. The first plan was truthfully
rejected after Nova inferred a $100 ceiling that could not include required monitoring. An explicit
$500 ceiling produced an App Runner recommendation estimated at $85 to $230 monthly using fixture
pricing. The review stayed `DRAFT` and `UNEXECUTED_REVIEW_ONLY`.

Invitation creation while delivery was disabled persisted a `FAILED` delivery record but returned
opaque HTTP 500. Cancellation then returned HTTP 200 and moved the test invitation to `CANCELLED`.

## Teardown

The failed test invitation was cancelled. The review-only planning records are retained as
immutable evidence. No customer infrastructure teardown was needed.

## Final boundary

No review was submitted or approved. No execution, deployment, mutation, or destruction of
customer infrastructure occurred.
