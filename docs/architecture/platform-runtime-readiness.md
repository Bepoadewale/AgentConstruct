# Platform runtime readiness

The AWS platform placement is an owner-operated pilot in account
`654654474502`, Region `us-east-1`, VPC `10.42.0.0/16`. It is separate from the
customer sandbox by VPC, state, IAM, names and tags, but remains in the same AWS
account.

## Two-stage activation

1. **Foundation:** ECR, runtime IAM, private encrypted RDS PostgreSQL, seven-day
   or longer backups, deletion protection, retained automated backups, final
   snapshot behavior, CloudWatch alarms, SNS and a tag-scoped AWS Budget. No NAT
   gateway or App Runner service is created in this stage.
2. **Hosted service:** App Runner, its VPC connector and one NAT gateway are
   created only after a reviewed immutable image, Google Workspace-compatible
   OIDC/JWKS settings and an HTTPS independent OPA endpoint are supplied.

The foundation is not a customer-ready deployment. A service without external
identity or policy is rejected before Terraform can apply it. Hosted mode never
uses the local signing-key or policy fixtures.

## Foundation plan and apply

Set the reviewed account, remote-state, Region, CloudFormation template and
operator notification variables. Never commit their values.

```bash
export EXPECTED_AWS_ACCOUNT_ID=654654474502
export AWS_REGION=us-east-1
export AGENTCONSTRUCT_PLATFORM_SCOPE=platform
export AGENTCONSTRUCT_PLATFORM_VPC_CIDR=10.42.0.0/16
export AGENTCONSTRUCT_ENABLE_DURABLE_DATABASE=true
export AGENTCONSTRUCT_ENABLE_NOVA_MODEL=true
export AGENTCONSTRUCT_ENABLE_RUNTIME_SERVICE=false
export AGENTCONSTRUCT_PLATFORM_MONTHLY_BUDGET_USD=250
export AGENTCONSTRUCT_ALERT_EMAIL='<operator email>'
./scripts/app-runner-runtime.sh plan
export CONFIRM_RUNTIME_FOUNDATION_APPLY=APPLY_AGENTCONSTRUCT_RUNTIME_FOUNDATION
./scripts/app-runner-runtime.sh apply-foundation
./scripts/platform-runtime-operations.sh verify-foundation
```

The email recipient must confirm the SNS subscription. AWS Budget email
notifications are direct and do not use that SNS confirmation.

## Nova activation evidence

Nova remains proposal-only. The fixed live evaluation sends two synthetic cases,
caps each response at 384 tokens, retains neither prompts nor outputs, and emits
request metadata and token counts. Pricing remains uncalculated unless a current,
versioned catalog is supplied.

```bash
EXPECTED_AWS_ACCOUNT_ID=654654474502 AWS_REGION=us-east-1 \
  .venv/bin/python scripts/nova_live_evaluation.py --output /tmp/nova-live-evidence.json
```

## Backup and recovery drill

```bash
export AGENTCONSTRUCT_PLATFORM_SNAPSHOT_ID="agentconstruct-runtime-manual-$(date -u +%Y%m%d%H%M%S)"
export CONFIRM_PLATFORM_SNAPSHOT=SNAPSHOT_AGENTCONSTRUCT_PLATFORM
./scripts/platform-runtime-operations.sh snapshot

export CONFIRM_PLATFORM_RESTORE_DRILL=RESTORE_AND_DELETE_AGENTCONSTRUCT_PLATFORM_DRILL
./scripts/platform-runtime-operations.sh restore-drill
```

The drill restores a temporary encrypted, private `db.t4g.micro`, verifies AWS
resource readiness, then deletes it. Before hosted identity exists, it cannot
query application rows from the private VPC, so it is infrastructure recovery
evidence—not a complete data-integrity or RTO claim.

## Hosted service gate

Service activation additionally requires:

```text
AGENTCONSTRUCT_RUNTIME_IMAGE_IDENTIFIER=<immutable ECR image URI:tag>
AGENTCONSTRUCT_JWKS_URL=https://...
AGENTCONSTRUCT_OIDC_ISSUER=https://...
AGENTCONSTRUCT_OIDC_AUDIENCE=<exact audience>
AGENTCONSTRUCT_OPA_URL=https://...
```

After a reviewed plan, set
`CONFIRM_RUNTIME_SERVICE_APPLY=APPLY_AGENTCONSTRUCT_RUNTIME_SERVICE`, apply, then
run `./scripts/platform-runtime-operations.sh verify-service`.

## Cost and security notes

- The idle foundation avoids an unused NAT gateway; RDS, snapshots, alarms and
  other enabled services can still incur charges.
- Activating App Runner with private RDS currently adds one NAT gateway so the
  connector can reach required public AWS and integration endpoints.
- Budget notifications are alerts, not automatic shutdown controls.
- The current terminal profile uses an IAM user. Replace it with SSO or another
  short-lived operator role before routine operations.
- A same-account VPC split does not provide cross-account blast-radius, billing,
  quota or administrator isolation.

References: [App Runner metrics](https://docs.aws.amazon.com/apprunner/latest/dg/monitor-cw.html),
[RDS metrics](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-metrics.html),
[Nova 2 Lite model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-lite.html),
and [AWS Budgets notifications](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_budgets_Notification.html).
