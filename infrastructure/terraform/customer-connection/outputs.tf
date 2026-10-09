output "discovery_role_arn" {
  value       = aws_iam_role.discovery.arn
  description = "Role for read-only inventory and Cost Explorer discovery."
}

output "execution_role_arn" {
  value       = aws_iam_role.execution_contract.arn
  description = "Empty-permission role reserved for a future approved execution profile."
}

output "credential_boundary" {
  value       = "AgentConstruct must use short-lived STS credentials with the external ID; no access key is created."
  description = "Human-readable safety boundary."
}
