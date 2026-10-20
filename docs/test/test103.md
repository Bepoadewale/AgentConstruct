# test103

Date: 2026-10-20
Execution type: Controlled live production customer journey with bounded fixture execution
Customer repository: No customer repository write; DavDeploy production control plane only
Commit: `4910d57dc67bda27f7bb0c6cc521610632a93a59`
AWS account: 654654474502
AWS region: us-east-1

## Resources created

- Three temporary Cognito users for the successful journey: administrator, developer, and outsider.
- One tenant, project, intent, architecture plan, customer plan revision, and associated audit and
  usage records.
- Two bounded fixture environments, staging and production.
- Zero customer cloud resources.

All temporary Cognito users were deleted. Both fixture environments were governed-destroyed.

## Commands executed

- Ran the authenticated production journey harness against
  `https://u885eka88l.execute-api.us-east-1.amazonaws.com`.
- Exercised onboarding and invitation acceptance with separate administrator and developer users.
- Exercised outsider tenant isolation, developer approval denial, and stale-digest denial.
- Generated the intent through Amazon Nova, created and reviewed the architecture plan, submitted
  the exact revision, and approved it as administrator.
- Executed the bounded staging and production environments through the production worker.
- Verified observed outputs and resources before starting governed teardown.
- Executed developer-authorized staging teardown and administrator-approved production teardown.
- Queried the live audit and usage APIs.
- Queried Aurora through the RDS Data API to audit all Live QA 103 environment states.
- Queried Cognito to verify temporary identity removal.

## Observed result

The final journey completed successfully with these identifiers:

- Project: `37151544-359e-48d6-8c5b-cf5a2b77371c`
- Intent: `4dae86ff-7bf4-4978-8915-14d32f49c87b`
- Architecture plan: `57ec33ee-3fd5-400f-945b-40126da28f81`
- Customer plan revision: `764e2b74-35d4-466b-a81d-6e693165afba`
- Selected profile: `aws-lambda-api`
- Staging final state: `DESTROYED`
- Production final state: `DESTROYED`
- Observed resource type: `lambda_function`
- Audit events observed: 22
- Model calls: 1
- Model input tokens: 707
- Model output tokens: 169
- Customer cloud resources created: 0

The READY observation contained `lambda_function_arn` and `lambda_function`. It contained neither
`app_runner_service_arn` nor `apprunner_service`.

Two preliminary harness attempts reached the live worker but ended because the harness used an
insufficient timeout and then assumed the wrong usage response shape. These were test harness
defects, not product execution failures. The final harness corrected both defects and passed.

## Teardown

The successful journey destroyed staging and production through the product APIs. A recovery pass
then used the same governed teardown APIs for the four fixture environments left by the two
preliminary attempts.

The final independent database query returned eight Live QA 103 environment records in total,
all with state `DESTROYED` and `cleanup_verified=true`. The final Cognito query returned zero
temporary `qa103-*` users. Local response files and temporary harnesses were removed.

## Final boundary

This run exercises the live control plane and bounded fixture worker only. It does not prove or
perform a real customer cloud deployment.
