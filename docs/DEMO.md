# Two-User Local Demonstration

The final two-browser approval demonstration is delivered after the customer-plan submission and decision UI slices. The current local product demo has separate signed `founder` developer and `administrator` workspace-administrator sign-in choices, dashboard views, and a server-side administrator-only pending-approval queue.

1. Developer selects fixture or authorised read-only GitHub/AWS connections, creates one plan and submits it.
2. Administrator opens the approval queue and approves or rejects the exact submitted revision.
3. Developer refreshes and sees the persisted result.
4. Administrator creates, submits and self-approves a separate plan; the audit identifies it as self-approval.

This demo never creates AWS infrastructure. Real GitHub/AWS modes remain explicit opt-in integrations.

## Connection flow available now

After local sign-in, select the fixture GitHub App installation, an authorized repository, and a branch. The local fixture does not call GitHub; a configured GitHub App runs the same list/inspect calls with a short-lived installation token and refuses writes. For AWS, choose an existing tenant-owned target or use **Connect AWS account** to open the customer-owned read-only role setup. The UI shows account, role, region, verification and capability information when available. It never asks for AWS access keys and does not grant deployment permission.
