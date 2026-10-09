package agentconstruct

default decision := {"result": "DENY", "reason": "deny by default"}

decision := {"result": "DENY", "reason": "requested budget exceeds the V1 safety limit"} if {
  input.action == "DEPLOY"
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

decision := {"result": "APPROVAL_REQUIRED", "reason": "production change needs an independent approval"} if {
  input.action == "CHANGE"
  input.target_environment_type == "production"
}

decision := {"result": "ALLOW", "reason": "non-production change is allowed"} if {
  input.action == "CHANGE"
  input.target_environment_type != "production"
}
