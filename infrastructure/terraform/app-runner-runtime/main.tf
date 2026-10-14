data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  name = "agentconstruct-runtime"
  tags = {
    Project   = "agentconstruct"
    ManagedBy = "terraform"
    Scope     = "control-plane-runtime"
    Purpose   = "live-customer-aws-connection-verification"
  }
  secret_prefix = trim(var.connection_secret_prefix, "/")
  runtime_env = {
    AGENTCONSTRUCT_DATABASE_URL                 = "sqlite+pysqlite:////tmp/agentconstruct.db"
    AGENTCONSTRUCT_WEB_ROOT                     = "/app/apps/web"
    AGENTCONSTRUCT_POLICY_FIXTURE               = "true"
    AGENTCONSTRUCT_AWS_LIVE_DISCOVERY_ENABLED   = "true"
    AGENTCONSTRUCT_AWS_VERIFY_INLINE            = "true"
    AGENTCONSTRUCT_CONNECTION_SECRET_BACKEND    = "aws_secrets_manager"
    AGENTCONSTRUCT_CONNECTION_SECRET_PREFIX     = local.secret_prefix
    AGENTCONSTRUCT_AWS_CONNECTION_TEMPLATE_URL  = var.customer_template_url
    AGENTCONSTRUCT_LOCAL_SIGNING_KEY_SECRET_ARN = aws_secretsmanager_secret.runtime_signing_key.arn
    AWS_DEFAULT_REGION                          = var.region
    AWS_REGION                                  = var.region
  }
}

resource "random_password" "runtime_signing_key" {
  length  = 48
  special = false
}

resource "aws_secretsmanager_secret" "runtime_signing_key" {
  name                    = "agentconstruct/runtime/local-signing-key"
  description             = "Temporary fixture signing key for the hosted AgentConstruct verification runtime."
  recovery_window_in_days = 0
  tags                    = local.tags
}

resource "aws_secretsmanager_secret_version" "runtime_signing_key" {
  secret_id     = aws_secretsmanager_secret.runtime_signing_key.id
  secret_string = random_password.runtime_signing_key.result
}

resource "aws_ecr_repository" "runtime" {
  name                 = local.name
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false

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
  name                 = "agentconstruct-apprunner-ecr-access"
  description          = "Allows App Runner to pull the AgentConstruct runtime image from ECR."
  assume_role_policy   = data.aws_iam_policy_document.apprunner_ecr_trust.json
  max_session_duration = 3600
  tags                 = local.tags
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
  name                 = "agentconstruct-control-plane-runtime"
  description          = "AWS-hosted AgentConstruct runtime identity for read-only customer AWS verification."
  assume_role_policy   = data.aws_iam_policy_document.runtime_trust.json
  max_session_duration = 3600
  tags                 = local.tags
}

data "aws_iam_policy_document" "runtime_permissions" {
  statement {
    sid       = "AssumeOnlyCustomerReadOnlyDiscoveryRoles"
    effect    = "Allow"
    actions   = ["sts:AssumeRole"]
    resources = ["arn:aws:iam::*:role/AgentConstructDiscovery-*"]
  }

  statement {
    sid    = "ManageConnectionExternalIds"
    effect = "Allow"
    actions = [
      "secretsmanager:CreateSecret",
      "secretsmanager:DescribeSecret",
      "secretsmanager:GetSecretValue",
      "secretsmanager:PutSecretValue",
      "secretsmanager:TagResource",
    ]
    resources = [
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${local.secret_prefix}/*"
    ]
  }

  statement {
    sid       = "ReadRuntimeFixtureSigningKey"
    effect    = "Allow"
    actions   = ["secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.runtime_signing_key.arn]
  }
}

resource "aws_iam_role_policy" "runtime_permissions" {
  name   = "agentconstruct-runtime-customer-discovery"
  role   = aws_iam_role.runtime.id
  policy = data.aws_iam_policy_document.runtime_permissions.json
}

resource "aws_cloudwatch_log_group" "runtime" {
  name              = "/aws/apprunner/${local.name}"
  retention_in_days = 14
  tags              = local.tags
}

resource "aws_apprunner_service" "runtime" {
  count        = var.enable_service ? 1 : 0
  service_name = local.name
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
        port = "8080"
        runtime_environment_variables = merge(local.runtime_env, {
          AGENTCONSTRUCT_CONTROL_PLANE_ROLE_ARN = aws_iam_role.runtime.arn
        })
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
    aws_cloudwatch_log_group.runtime,
    aws_iam_role_policy.runtime_permissions,
    aws_iam_role_policy_attachment.apprunner_ecr_access,
    aws_secretsmanager_secret_version.runtime_signing_key,
  ]
}
