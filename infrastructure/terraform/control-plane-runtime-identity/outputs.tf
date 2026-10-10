output "runtime_role_arn" {
  value       = aws_iam_role.runtime.arn
  description = "Use this ARN in the public customer CloudFormation template; never use the GitHub Actions role."
}
