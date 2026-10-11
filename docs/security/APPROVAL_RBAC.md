# Approval RBAC

| Role | Allowed | Not allowed |
| --- | --- | --- |
| Developer | Create, revise and submit their workspace plans | Approve or reject any plan; gain another tenant's access |
| Workspace administrator | Create, revise, submit, approve and reject workspace plans | Bypass plan integrity, policy or cloud permissions |

Administrators may approve their own submitted customer plan in this product phase. The decision records `is_self_approval=true`, creator, approver, revision, digest, policy and time. This exception applies only to customer plan decisions. It does not make an administrator an AWS administrator and does not auto-deploy a plan.
