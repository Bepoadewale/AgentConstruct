output "api_base_url" {
  description = "Public HTTPS API base URL for VITE_API_BASE_URL."
  value       = aws_apigatewayv2_api.control_plane.api_endpoint
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.identity.id
}

output "cognito_client_id" {
  value = aws_cognito_user_pool_client.frontend.id
}

output "cognito_issuer" {
  value = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.identity.id}"
}

output "cognito_managed_login_base_url" {
  value = "https://${aws_cognito_user_pool_domain.identity.domain}.auth.${var.region}.amazoncognito.com"
}

output "database_cluster_arn" {
  value = aws_rds_cluster.control_plane.arn
}

output "migration_function_name" {
  value = aws_lambda_function.migrate.function_name
}

output "worker_dead_letter_queue_url" {
  value = aws_sqs_queue.worker_dead_letter.url
}
