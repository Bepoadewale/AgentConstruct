output "cluster_name" { value = module.eks.cluster_name }
output "ecr_repository_url" { value = module.ecr.repository_url }
output "artifact_bucket_name" { value = module.artifacts.bucket_name }
output "database_secret_arn" { value = module.rds.master_secret_arn }
output "application_secret_arn" { value = aws_secretsmanager_secret.application.arn }
output "workload_role_arn" { value = module.workload_iam.workload_role_arn }
