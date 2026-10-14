output "ecr_repository_url" {
  value       = aws_ecr_repository.customer_workload.repository_url
  description = "ECR repository for the customer workload image."
}

output "app_runner_service_url" {
  value       = var.enable_service ? "https://${aws_apprunner_service.customer_workload[0].service_url}" : null
  description = "Customer workload App Runner URL when enabled."
}

output "app_runner_service_arn" {
  value       = var.enable_service ? aws_apprunner_service.customer_workload[0].arn : null
  description = "Customer workload App Runner service ARN when enabled."
}

output "runtime_role_arn" {
  value       = aws_iam_role.runtime.arn
  description = "Minimal App Runner runtime role for the customer workload pilot."
}

output "pilot_scope" {
  value = {
    execution_boundary = "REAL_AWS_CREATE_VALIDATE_DESTROY"
    source_repository  = var.source_repository
    source_commit      = var.source_commit
    plan_digest        = var.plan_digest
  }
}
