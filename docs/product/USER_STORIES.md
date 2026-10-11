# User Stories

- A developer can create a project, select authorised GitHub and AWS connections, describe an outcome, review one AWS plan and submit it.
- An administrator can review every submitted plan in their workspace, approve it or reject it with a reason.
- An administrator can submit and approve their own plan. The record must state that it was self-approved.
- A developer cannot approve or reject through the UI or a direct API call.
- A submitted revision is immutable. A changed plan becomes a new draft revision and needs a new decision.
- An approved plan is not a deployed plan.
