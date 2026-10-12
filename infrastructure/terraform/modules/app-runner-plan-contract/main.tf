locals {
  execution_boundary = "PLAN_ONLY_NOT_APPLIED"

  app_runner_contract = {
    service = {
      profile    = var.profile
      name       = var.service_name
      region     = var.aws_region
      account_id = var.aws_account_id
      source     = var.source_boundary
      image      = var.image_repository
    }

    repository = {
      url    = var.repository_url
      branch = var.repository_branch
    }

    iam = var.iam

    configuration = {
      environment_variables = var.environment_variables
      secret_references     = var.secret_references
      https_access          = var.https_access
    }

    observability = var.observability
    tags          = var.tags

    evidence = {
      project_id                = var.project_id
      revision_id               = var.revision_id
      source_deployment_plan_id = var.source_deployment_plan_id
      plan_digest               = var.plan_digest
      execution_boundary        = local.execution_boundary
      apply_command_available   = false
    }
  }
}
