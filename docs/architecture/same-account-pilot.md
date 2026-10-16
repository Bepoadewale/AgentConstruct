# Same-account platform and customer-sandbox pilot

The controlled pilot uses one AWS account because the repository owner has
explicitly prohibited creation of AWS Organizations member accounts. It uses
separate placement contracts inside account `654654474502`:

| Placement | Scope tag | VPC CIDR | Terraform state key |
| --- | --- | --- | --- |
| AgentConstruct platform | `platform` | `10.42.0.0/16` | `agentconstruct/platform/app-runner-runtime.tfstate` |
| Customer sandbox | `customer-sandbox` | `10.84.0.0/16` | `agentconstruct/customer-sandbox/workload-app-runner.tfstate` |

Both placements carry `AccountBoundary=same-account-pilot`. The customer
sandbox output states `SAME_ACCOUNT_PILOT_NOT_CROSS_ACCOUNT`; UI, audit and test
evidence must preserve that limitation.

## Enforced boundaries

- Exact account and Region checks run before Terraform operations.
- Platform and customer resources use different names, VPCs, subnets, security
  groups, IAM roles, tags and state keys.
- The customer workload VPC has private subnets, no internet gateway and no NAT
  gateway. Its App Runner VPC connector has no default egress rule.
- The customer workload runtime role has no cloud permissions.
- Destructive commands require exact confirmation text.
- Customer teardown verifies absence of its App Runner service, ECR repository,
  tagged VPC and named runtime roles.
- No automation creates or invites an AWS Organizations account.

## What this does not prove

A VPC is a network boundary, not an AWS account boundary. Platform and customer
resources still share the same account administrator, service quotas, billing,
CloudTrail administration and ultimate IAM control. This pilot is suitable for
owner-controlled design-partner evidence only. It must not be described as
cross-account tenant isolation or used as the long-term boundary for unrelated
customers.

## Operator variables

```text
EXPECTED_AWS_ACCOUNT_ID=654654474502
AWS_REGION=us-east-1
AGENTCONSTRUCT_PLATFORM_SCOPE=platform
AGENTCONSTRUCT_PLATFORM_VPC_CIDR=10.42.0.0/16
AGENTCONSTRUCT_CUSTOMER_DEPLOYMENT_SCOPE=customer-sandbox
AGENTCONSTRUCT_CUSTOMER_VPC_CIDR=10.84.0.0/16
```

Account creation, Organization invitation and account deletion are outside the
pilot scripts. Deleting the customer sandbox means running its bounded Terraform
destroy and absence verification; it does not mean deleting the shared AWS
account.
