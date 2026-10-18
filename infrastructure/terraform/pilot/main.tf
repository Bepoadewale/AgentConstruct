locals {
  tags = { Project = var.project, Environment = var.environment, ManagedBy = "terraform", Scope = "cloud-pilot-contract" }
}

module "vpc" {
  source = "../modules/vpc"
  name   = "${var.project}-${var.environment}"
  cidr   = var.vpc_cidr
  azs    = var.availability_zones
  tags   = local.tags
}
module "ecr" {
  source = "../modules/ecr"
  name   = "${var.project}-api"
  tags   = local.tags
}
module "artifacts" {
  source = "../modules/artifacts"
  name   = "${var.project}-${var.environment}-artifacts"
  tags   = local.tags
}
module "eks" {
  source     = "../modules/eks"
  name       = "${var.project}-${var.environment}"
  subnet_ids = module.vpc.private_subnet_ids
  tags       = local.tags
}
resource "aws_secretsmanager_secret" "application" {
  name = "${var.project}/${var.environment}/application"
  tags = local.tags
}
module "workload_iam" {
  source            = "../modules/iam"
  name              = "${var.project}-${var.environment}"
  oidc_issuer       = module.eks.oidc_issuer
  oidc_provider_arn = module.eks.oidc_provider_arn
  namespace         = "davdeploy"
  service_account   = "davdeploy-api"
  secret_arns       = [module.rds.master_secret_arn, aws_secretsmanager_secret.application.arn]
  tags              = local.tags
}
module "rds" {
  source     = "../modules/rds"
  name       = "${var.project}-${var.environment}"
  subnet_ids = module.vpc.private_subnet_ids
  vpc_id     = module.vpc.vpc_id
  tags       = local.tags
}
