# test95

Date: 2026-10-19
Execution type: Real AWS reconciliation evidence plus static and local validation
Customer repository: `Bepoadewale/davdeploy`
Commit: PR #95 branch, final implementation commit recorded in Git history
AWS account: `654654474502`
AWS region: `us-east-1`

## Resources created

Apply run `39271445733` created API Gateway HTTP API `u885eka88l` and JWT authorizer
`2yw36k`. It also updated the existing `davdeploy-policy` and `davdeploy-cognito-link`
Lambda packages. Terraform recorded successful changes in remote state.

## Commands executed

- `gh run view 39271445733 --log-failed`
- Focused bootstrap policy regression tests
- Terraform validation for every root
- Repository verification suite
- State-aware production plan after the policy update

## Observed result

The apply stopped safely before completion. The remaining authorization failures were limited to
creating Aurora's RDS-managed master-password secret and tagging the API Gateway stage. This PR
adds only those scoped permissions and regression assertions.

The state-aware production plan completed with 12 additions, 0 changes, and 0 destroys.

## Teardown

No teardown was performed because the successfully created resources are part of the intended
production control plane and remain recorded in Terraform state.

## Final boundary

This PR does not apply infrastructure or edit Terraform state. A fresh saved plan is required after
merge. A successful local or CI validation does not prove that the next AWS apply will succeed.
