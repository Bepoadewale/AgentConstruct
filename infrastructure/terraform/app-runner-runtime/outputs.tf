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

output "database_endpoint" {
  value       = var.enable_durable_database ? aws_db_instance.control_plane[0].address : null
  description = "Private RDS PostgreSQL endpoint for the hosted AgentConstruct control plane."
}

output "database_secret_arn" {
  value       = var.enable_durable_database ? aws_db_instance.control_plane[0].master_user_secret[0].secret_arn : null
  description = "AWS-managed Secrets Manager ARN for the RDS master credential. The secret value is never committed."
}

output "runtime_vpc_connector_arn" {
  value       = var.enable_service && var.enable_durable_database ? aws_apprunner_vpc_connector.runtime[0].arn : null
  description = "App Runner VPC connector used to reach the private control-plane database."
}

output "platform_vpc_id" {
  value       = var.enable_durable_database ? aws_vpc.runtime[0].id : null
  description = "Dedicated same-account AgentConstruct platform VPC."
}

output "platform_private_subnet_ids" {
  value       = var.enable_durable_database ? aws_subnet.private[*].id : []
  description = "Private platform subnets containing RDS and, after activation, the App Runner connector."
}

output "platform_alert_topic_arn" {
  value       = aws_sns_topic.platform_alerts.arn
  description = "SNS topic used by actionable platform alarms. Email subscriptions require confirmation."
}

output "platform_budget_name" {
  value       = aws_budgets_budget.platform.name
  description = "Tag-scoped monthly platform budget guardrail."
}

output "database_alarm_names" {
  value = var.enable_durable_database ? [
    aws_cloudwatch_metric_alarm.database_cpu_high[0].alarm_name,
    aws_cloudwatch_metric_alarm.database_storage_low[0].alarm_name,
    aws_cloudwatch_metric_alarm.database_connections_high[0].alarm_name,
  ] : []
  description = "CloudWatch database alarms created for the durable platform."
}

output "service_activation_state" {
  value       = var.enable_service ? "HOSTED_SERVICE_ENABLED" : "FOUNDATION_ONLY_IDENTITY_AND_POLICY_REQUIRED"
  description = "Explicitly distinguishes a platform foundation from a customer-ready hosted service."
}
