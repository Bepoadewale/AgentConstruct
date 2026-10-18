package davdeploy

test_budget_is_denied if {
  decision := data.davdeploy.decision with input as {"spec": {"monthly_budget_usd": 2000, "environments": ["staging"]}, "action": "DEPLOY"}
  decision.result == "DENY"
}

test_production_needs_approval if {
  decision := data.davdeploy.decision with input as {"spec": {"monthly_budget_usd": 1200, "environments": ["production"]}, "action": "DEPLOY"}
  decision.result == "APPROVAL_REQUIRED"
}

test_safe_staging_is_allowed if {
  decision := data.davdeploy.decision with input as {"spec": {"monthly_budget_usd": 1200, "environments": ["staging"]}, "action": "DEPLOY"}
  decision.result == "ALLOW"
}
