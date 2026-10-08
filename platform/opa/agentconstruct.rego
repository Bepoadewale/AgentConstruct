package agentconstruct

default decision := {"result": "DENY", "reason": "deny by default"}

decision := {"result": "DENY", "reason": "requested budget exceeds the V1 safety limit"} if {
  input.spec.monthly_budget_usd > 1500
}

decision := {"result": "APPROVAL_REQUIRED", "reason": "production deployment needs an independent approval"} if {
  input.action == "DEPLOY"
  input.spec.environments[_] == "production"
  input.spec.monthly_budget_usd <= 1500
}

decision := {"result": "ALLOW", "reason": "development-only deployment is allowed"} if {
  input.action == "DEPLOY"
  not "production" in input.spec.environments
  input.spec.monthly_budget_usd <= 1500
}
