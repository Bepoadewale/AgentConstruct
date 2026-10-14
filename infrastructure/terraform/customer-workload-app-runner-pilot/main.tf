data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  tags = {
    Project                    = "agentconstruct"
    ManagedBy                  = "terraform"
    Scope                      = "customer-workload-pilot"
    Purpose                    = "real-app-runner-create-validate-destroy"
    AgentConstructPlanDigest   = var.plan_digest
    AgentConstructSourceRepo   = "Bepoadewale/ai-platform-control-plane"
    AgentConstructSourceCommit = substr(var.source_commit, 0, 12)
  }
}

resource "terraform_data" "account_guard" {
  input = data.aws_caller_identity.current.account_id

  lifecycle {
    precondition {
      condition     = data.aws_caller_identity.current.account_id == var.expected_account_id
      error_message = "AWS account guard failed. This pilot may only run in the expected customer account."
    }

    precondition {
      condition     = data.aws_region.current.name == var.region
      error_message = "AWS region guard failed. Re-run in the explicitly selected customer region."
    }

    precondition {
      condition     = !var.enable_service || var.image_identifier != "placeholder.invalid/agentconstruct-customer-workload:unset"
      error_message = "image_identifier must be set before enabling the App Runner service."
    }
  }
}

resource "aws_ecr_repository" "customer_workload" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = local.tags
}

data "aws_iam_policy_document" "apprunner_ecr_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["build.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "apprunner_ecr_access" {
  name                 = "agentconstruct-customer-apprunner-ecr"
  description          = "Allows App Runner to pull the AgentConstruct customer workload pilot image from ECR."
  assume_role_policy   = data.aws_iam_policy_document.apprunner_ecr_trust.json
  max_session_duration = 3600
  tags                 = local.tags

  depends_on = [terraform_data.account_guard]
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr_access" {
  role       = aws_iam_role.apprunner_ecr_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

data "aws_iam_policy_document" "runtime_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["tasks.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "runtime" {
  name                 = "agentconstruct-customer-apprunner-runtime"
  description          = "Minimal App Runner runtime role for the AgentConstruct customer workload pilot."
  assume_role_policy   = data.aws_iam_policy_document.runtime_trust.json
  max_session_duration = 3600
  tags                 = local.tags

  depends_on = [terraform_data.account_guard]
}

resource "aws_cloudwatch_log_group" "customer_workload" {
  name              = "/aws/apprunner/${var.service_name}"
  retention_in_days = 3
  tags              = local.tags
}

resource "aws_apprunner_service" "customer_workload" {
  count        = var.enable_service ? 1 : 0
  service_name = var.service_name
  tags         = local.tags

  source_configuration {
    auto_deployments_enabled = false

    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr_access.arn
    }

    image_repository {
      image_identifier      = var.image_identifier
      image_repository_type = "ECR"

      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          PLATFORM_AUTH_MODE              = "headers"
          PLATFORM_ALLOW_INSECURE_HEADERS = "true"
          PLATFORM_OPA_DECISION_URL       = "fixture-disabled-for-healthz-only"
          PLATFORM_CONTROL_PLANE_DB       = "/app/state/control-plane.db"
          AGENTCONSTRUCT_PLAN_DIGEST      = var.plan_digest
          AGENTCONSTRUCT_SOURCE_REPO      = var.source_repository
          AGENTCONSTRUCT_SOURCE_COMMIT    = var.source_commit
        }
      }
    }
  }

  instance_configuration {
    cpu               = var.cpu
    memory            = var.memory
    instance_role_arn = aws_iam_role.runtime.arn
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/healthz"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }

  depends_on = [
    terraform_data.account_guard,
    aws_cloudwatch_log_group.customer_workload,
    aws_iam_role_policy_attachment.apprunner_ecr_access,
  ]
}
