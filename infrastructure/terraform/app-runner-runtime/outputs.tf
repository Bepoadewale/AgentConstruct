output "ecr_repository_url" {
  value       = aws_ecr_repository.runtime.repository_url
  description = "ECR repository for the AgentConstruct runtime image."
}

output "runtime_role_arn" {
  value       = aws_iam_role.runtime.arn
  description = "Use this ARN as AgentConstructControlPlaneRoleArn in customer CloudFormation templates."
}

output "app_runner_service_url" {
  value       = var.enable_service ? "https://${aws_apprunner_service.runtime[0].service_url}" : null
  description = "Hosted AgentConstruct runtime URL when the service is enabled."
}

output "app_runner_service_arn" {
  value       = var.enable_service ? aws_apprunner_service.runtime[0].arn : null
  description = "Hosted AgentConstruct App Runner service ARN when enabled."
}
