# Two-User Local Demonstration

The final two-browser demonstration is delivered after the dashboard and approval UI slices. It will use the local `founder` developer fixture and `operator` administrator fixture in separate browser sessions.

1. Developer selects fixture or authorised read-only GitHub/AWS connections, creates one plan and submits it.
2. Administrator opens the approval queue and approves or rejects the exact submitted revision.
3. Developer refreshes and sees the persisted result.
4. Administrator creates, submits and self-approves a separate plan; the audit identifies it as self-approval.

This demo never creates AWS infrastructure. Real GitHub/AWS modes remain explicit opt-in integrations.
