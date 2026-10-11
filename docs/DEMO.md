# Two-User Local Demonstration

The local product demo has separate signed `founder` developer and `administrator` workspace-administrator sign-in choices, dashboard views, a server-side administrator-only pending-approval queue, and persisted customer-plan decisions. This is a local fixture identity flow, not enterprise sign-in.

1. In Browser A, sign in as **developer**, select fixture or authorised read-only GitHub/AWS connections, create one plan, and select **Submit for approval**.
2. In Browser B, sign in as **administrator**, open the pending plan from the dashboard, then approve or reject the exact submitted digest. Rejection requires a reason.
3. Return to Browser A, refresh the dashboard or reopen the revision, and see the persisted result. A rejected plan can create a new immutable draft revision.
4. In Browser B, create, submit and approve an administrator-owned plan. Its audit event and decision record identify `is_self_approval: true`.

This demo never creates AWS infrastructure. Real GitHub/AWS modes remain explicit opt-in integrations.

## Connection flow available now

After local sign-in, select the fixture GitHub App installation, an authorized repository, and a branch. The local fixture does not call GitHub; a configured GitHub App runs the same list/inspect calls with a short-lived installation token and refuses writes. For AWS, choose an existing tenant-owned target or use **Connect AWS account** to open the customer-owned read-only role setup. The UI shows account, role, region, verification and capability information when available. It never asks for AWS access keys and does not grant deployment permission.
