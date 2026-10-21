# test119

Date: 2026-10-22
Execution type: Real authenticated production control-plane journey, review-only customer planning
Customer repository: `https://github.com/Bepoadewale/ai-platform-control-plane`
Commit: `d4ed0a88d7c585e2de17d7e2c50cebd449a983ad`
AWS account: Existing DavDeploy control-plane account
AWS region: `us-east-1`

## Release evidence

- Migration-compatible package plan run `39689372085`: 0 add, 5 in-place Lambda updates,
  0 destroy.
- Migration-compatible apply run `39689527422`: saved plan applied, OIDC session refreshed, and
  database migration completed successfully.
- Customer-response correction plan run `39691003131`: 0 add, 5 in-place Lambda updates,
  0 destroy.
- Customer-response correction apply run `39691176811`: saved plan applied and database migration
  verification completed successfully.

## Resources created

- User: `ec34012e-37b4-4b5e-886c-47723a9a61dd`, administrator.
- Workspace: `ae7eb954-c8a9-4280-8c0a-79873bf46771`.
- Project: `69e77ebe-5614-4ea2-95ab-5a3f78d966ca`.
- First intent: `aa31444b-1731-43f7-8f25-3c2a990bcc1a`.
- Successful explicit-budget intent: `f7490d54-913b-45cb-8f51-8eeb81ae9c32`.
- Architecture plan: `b73dc2fe-28d2-445e-ba84-67860a8bc63c`.
- Draft customer review: `d2c4f3dc-f0ab-4971-bfb3-cab7b83193c`, revision 1, content digest
  `947365a0b7e1a7673182c7326f261aaad57990072c9b203214817058bb01cc9f`.
- Cancelled invitation records: `b062a99d-1148-414f-adfd-ae116a6be929` and
  `1026cc14-e10d-4c98-b09b-13366ebc2395`.

## Commands executed

- Cognito choice-based `USER_AUTH` with email OTP and a short-lived ID token.
- Authenticated `GET /api/v1/me` and `GET /api/v1/workspace/invitations`.
- Project creation and public read-only GitHub repository discovery.
- Two intent creations and architecture-plan requests.
- Draft customer-review creation only.
- Invitation create, list, and cancel checks while email delivery remained disabled.
- Local `python3.12 scripts/check_doc_conventions.py` and `git diff --check` for this evidence PR.

## Observed result

The authenticated user resolved as an administrator in the expected workspace. Public repository
discovery executed read-only against branch `main` and detected Python, FastAPI, PostgreSQL,
environment-secret, and GitHub Actions evidence with confidence 0.82.

Nova 2 Lite interpreted both requests using Bedrock. The first request inferred a $100 monthly
ceiling. Planning returned HTTP 409 because every viable option with required Prometheus and
Grafana monitoring exceeded that ceiling. No false plan was persisted.

The second request explicitly set a $500 monthly ceiling, 10 average requests per second, 20 peak
requests per second, 99.9 percent availability, and `us-east-1`. Planning selected the simplest
viable managed application profile using App Runner, Secrets Manager, Amazon Managed Service for
Prometheus, and Amazon Managed Grafana. The fixture estimate was $85 to $230 monthly, operational
complexity 1/5, and policy result `APPROVAL_REQUIRED`. This is an estimate using fixture pricing,
not an actual AWS bill.

The customer review was created in `DRAFT` state with execution marker
`UNEXECUTED_REVIEW_ONLY`. It was not submitted or approved.

After the final release, disabled invitation delivery returned HTTP 503 with detail
`workspace invitation email delivery is not configured`. Both test invitation records remained
observable with `delivery_state=FAILED`, then cancellation returned HTTP 200 and moved each record
to `CANCELLED`.

## Teardown

Both test invitation records were cancelled. Short-lived local authentication artifacts are
removed after evidence capture. Review-only planning records remain as immutable control-plane
evidence. No customer resource teardown was required.

## Final boundary

No customer review was submitted or approved. No customer cloud connection was used. No Terraform,
shell, deployment, execution, mutation, change, or destroy operation ran against customer
infrastructure.

Automatic invitation email delivery is implemented but remains disabled in production until a
verified SES sender and production sending access are configured.
