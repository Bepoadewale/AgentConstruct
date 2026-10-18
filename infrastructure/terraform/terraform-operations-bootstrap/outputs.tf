output "state_bucket_name" {
  value = data.aws_s3_bucket.state.id
}

output "lock_table_name" {
  value = data.aws_dynamodb_table.lock.name
}

output "plan_bucket_name" {
  value = aws_s3_bucket.plans.id
}

output "plan_kms_key_arn" {
  value = aws_kms_key.plans.arn
}

output "release_bucket_name" {
  value = aws_s3_bucket.releases.id
}

output "release_kms_key_arn" {
  value = aws_kms_key.releases.arn
}

output "terraform_plan_role_arn" {
  value = aws_iam_role.plan.arn
}

output "terraform_apply_role_arn" {
  value = aws_iam_role.apply.arn
}
