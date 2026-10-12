output "contract" {
  description = "Plan-only App Runner deployment contract. It creates no AWS resources."
  value       = local.app_runner_contract
}

output "execution_boundary" {
  description = "This module intentionally renders a contract only."
  value       = local.execution_boundary
}

output "apply_command_available" {
  description = "Always false. Apply is not exposed from this renderer."
  value       = false
}
