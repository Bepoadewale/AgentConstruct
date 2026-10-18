locals {
  name = "agentconstruct-${var.environment}"
  common_tags = {
    Product     = "AgentConstruct"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

resource "aws_vpc" "database" {
  cidr_block           = "10.44.0.0/20"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = merge(local.common_tags, { Name = "${local.name}-database" })
}

resource "aws_subnet" "database" {
  count             = 2
  vpc_id            = aws_vpc.database.id
  cidr_block        = cidrsubnet(aws_vpc.database.cidr_block, 4, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags              = merge(local.common_tags, { Name = "${local.name}-database-${count.index + 1}" })
}

resource "aws_db_subnet_group" "control_plane" {
  name       = local.name
  subnet_ids = aws_subnet.database[*].id
  tags       = local.common_tags
}

resource "aws_security_group" "database" {
  name        = "${local.name}-database"
  description = "Aurora has no network clients; application access uses the Data API"
  vpc_id      = aws_vpc.database.id
  tags        = local.common_tags
}

resource "aws_rds_cluster" "control_plane" {
  cluster_identifier              = local.name
  engine                          = "aurora-postgresql"
  engine_mode                     = "provisioned"
  engine_version                  = var.aurora_engine_version
  database_name                   = var.database_name
  master_username                 = "agentconstruct_admin"
  manage_master_user_password     = true
  enable_http_endpoint            = true
  db_subnet_group_name            = aws_db_subnet_group.control_plane.name
  vpc_security_group_ids          = [aws_security_group.database.id]
  backup_retention_period         = 7
  preferred_backup_window         = "03:00-04:00"
  storage_encrypted               = true
  deletion_protection             = var.database_deletion_protection
  skip_final_snapshot             = false
  final_snapshot_identifier       = "${local.name}-final"
  apply_immediately               = false
  enabled_cloudwatch_logs_exports = ["postgresql"]

  serverlessv2_scaling_configuration {
    min_capacity             = var.aurora_min_capacity
    max_capacity             = var.aurora_max_capacity
    seconds_until_auto_pause = var.aurora_min_capacity == 0 ? var.aurora_seconds_until_auto_pause : null
  }

  tags = local.common_tags
}

resource "aws_rds_cluster_instance" "control_plane" {
  identifier         = "${local.name}-1"
  cluster_identifier = aws_rds_cluster.control_plane.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.control_plane.engine
  engine_version     = aws_rds_cluster.control_plane.engine_version
  tags               = local.common_tags
}

resource "aws_cognito_user_pool" "identity" {
  name                     = local.name
  user_pool_tier           = "ESSENTIALS"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  mfa_configuration        = "OFF"

  sign_in_policy {
    allowed_first_auth_factors = ["PASSWORD", "EMAIL_OTP"]
  }

  password_policy {
    minimum_length                   = 12
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 7
  }

  email_configuration {
    email_sending_account  = var.ses_identity_arn == "" ? "COGNITO_DEFAULT" : "DEVELOPER"
    source_arn             = var.ses_identity_arn == "" ? null : var.ses_identity_arn
    from_email_address     = var.ses_identity_arn == "" ? null : var.ses_from_address
    reply_to_email_address = var.ses_identity_arn == "" ? null : var.ses_from_address
  }

  lambda_config {
    pre_sign_up = aws_lambda_function.cognito_link.arn
  }

  deletion_protection = "ACTIVE"
  tags                = local.common_tags
}

resource "aws_cognito_user_pool_client" "frontend" {
  name         = "${local.name}-frontend"
  user_pool_id = aws_cognito_user_pool.identity.id

  generate_secret                      = false
  prevent_user_existence_errors        = "ENABLED"
  enable_token_revocation              = true
  read_attributes                      = ["email", "email_verified", "name"]
  supported_identity_providers         = var.google_identity_provider_enabled ? ["COGNITO", "Google"] : ["COGNITO"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  callback_urls                        = ["${var.frontend_origin}/auth/callback"]
  logout_urls                          = [var.frontend_origin]
  explicit_auth_flows                  = ["ALLOW_USER_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  access_token_validity                = 15
  id_token_validity                    = 15
  refresh_token_validity               = 7

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}

resource "aws_cognito_user_pool_domain" "identity" {
  domain       = var.cognito_domain_prefix
  user_pool_id = aws_cognito_user_pool.identity.id
}

resource "aws_iam_role" "api" {
  name = "${local.name}-api"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "api_logs" {
  role       = aws_iam_role.api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "api" {
  name = "control-plane-access"
  role = aws_iam_role.api.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["rds-data:BatchExecuteStatement", "rds-data:BeginTransaction", "rds-data:CommitTransaction", "rds-data:ExecuteStatement", "rds-data:RollbackTransaction"]
        Resource = aws_rds_cluster.control_plane.arn
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = aws_rds_cluster.control_plane.master_user_secret[0].secret_arn
      },
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = aws_lambda_function.policy.arn
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
        Resource = "arn:aws:bedrock:*::foundation-model/*"
      }
    ]
  })
}

resource "aws_iam_role" "policy" {
  name = "${local.name}-policy"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "policy_logs" {
  role       = aws_iam_role.policy.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "cognito_link" {
  name = "${local.name}-cognito-link"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "cognito_link_logs" {
  role       = aws_iam_role.cognito_link.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "cognito_link" {
  name = "link-verified-google-identities"
  role = aws_iam_role.cognito_link.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["cognito-idp:ListUsers", "cognito-idp:AdminLinkProviderForUser"]
      Resource = aws_cognito_user_pool.identity.arn
    }]
  })
}

resource "aws_lambda_function" "policy" {
  function_name     = "${local.name}-policy"
  role              = aws_iam_role.policy.arn
  runtime           = "python3.12"
  handler           = "agentconstruct.lambda_policy.handler"
  s3_bucket         = var.artifact_bucket
  s3_key            = var.artifact_key
  s3_object_version = var.artifact_object_version
  timeout           = 5
  memory_size       = 256
  tags              = local.common_tags
}

resource "aws_lambda_function" "cognito_link" {
  function_name     = "${local.name}-cognito-link"
  role              = aws_iam_role.cognito_link.arn
  runtime           = "python3.12"
  handler           = "agentconstruct.lambda_cognito_link.handler"
  s3_bucket         = var.artifact_bucket
  s3_key            = var.artifact_key
  s3_object_version = var.artifact_object_version
  timeout           = 10
  memory_size       = 256
  tags              = local.common_tags
}

resource "aws_lambda_permission" "cognito_link" {
  statement_id  = "AllowCognito"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_link.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.identity.arn
}

locals {
  runtime_environment = {
    AGENTCONSTRUCT_HOSTED_MODE              = "true"
    AGENTCONSTRUCT_AUTO_MIGRATE             = "false"
    AGENTCONSTRUCT_AURORA_CLUSTER_ARN       = aws_rds_cluster.control_plane.arn
    AGENTCONSTRUCT_DATABASE_SECRET_ARN      = aws_rds_cluster.control_plane.master_user_secret[0].secret_arn
    AGENTCONSTRUCT_DATABASE_NAME            = var.database_name
    AGENTCONSTRUCT_ALLOWED_FRONTEND_ORIGINS = var.frontend_origin
    AGENTCONSTRUCT_JWKS_URL                 = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.identity.id}/.well-known/jwks.json"
    AGENTCONSTRUCT_OIDC_ISSUER              = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.identity.id}"
    AGENTCONSTRUCT_OIDC_AUDIENCE            = aws_cognito_user_pool_client.frontend.id
    AGENTCONSTRUCT_POLICY_FUNCTION_ARN      = aws_lambda_function.policy.arn
    AGENTCONSTRUCT_MODEL_PROVIDER           = "bedrock-nova"
    AGENTCONSTRUCT_BEDROCK_MODEL_ID         = var.nova_model_id
  }
}

resource "aws_lambda_function" "api" {
  function_name     = "${local.name}-api"
  role              = aws_iam_role.api.arn
  runtime           = "python3.12"
  handler           = "agentconstruct.lambda_api.handler"
  s3_bucket         = var.artifact_bucket
  s3_key            = var.artifact_key
  s3_object_version = var.artifact_object_version
  timeout           = 29
  memory_size       = 1024

  environment {
    variables = local.runtime_environment
  }
  tags = local.common_tags
}

resource "aws_lambda_function" "migrate" {
  function_name     = "${local.name}-migrate"
  role              = aws_iam_role.api.arn
  runtime           = "python3.12"
  handler           = "agentconstruct.lambda_migrate.handler"
  s3_bucket         = var.artifact_bucket
  s3_key            = var.artifact_key
  s3_object_version = var.artifact_object_version
  timeout           = 300
  memory_size       = 1024

  environment {
    variables = local.runtime_environment
  }
  tags = local.common_tags
}

resource "aws_apigatewayv2_api" "control_plane" {
  name          = local.name
  protocol_type = "HTTP"

  cors_configuration {
    allow_credentials = false
    allow_headers     = ["Authorization", "Content-Type", "Idempotency-Key"]
    allow_methods     = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    allow_origins     = [var.frontend_origin]
    expose_headers    = ["X-AgentConstruct-API-Version", "X-Request-ID", "X-Correlation-ID"]
    max_age           = 600
  }
  tags = local.common_tags
}

resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.control_plane.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "cognito"

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.frontend.id]
    issuer   = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.identity.id}"
  }
}

resource "aws_apigatewayv2_integration" "api" {
  api_id                 = aws_apigatewayv2_api.control_plane.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 29000
}

resource "aws_apigatewayv2_route" "authenticated" {
  api_id             = aws_apigatewayv2_api.control_plane.id
  route_key          = "$default"
  target             = "integrations/${aws_apigatewayv2_integration.api.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.control_plane.id
  route_key = "GET /healthz"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.control_plane.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 50
    throttling_rate_limit  = 25
  }
  tags = local.common_tags
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowApiGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.control_plane.execution_arn}/*/*"
}

resource "aws_sqs_queue" "worker_dead_letter" {
  name                      = "${local.name}-worker-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
  tags                      = local.common_tags
}

resource "aws_sqs_queue" "worker" {
  name                       = "${local.name}-worker"
  visibility_timeout_seconds = 360
  message_retention_seconds  = 345600
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.worker_dead_letter.arn
    maxReceiveCount     = 5
  })
  tags = local.common_tags
}

resource "aws_iam_role_policy" "worker_queue" {
  name = "worker-queue"
  role = aws_iam_role.api.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
      Resource = aws_sqs_queue.worker.arn
    }]
  })
}

resource "aws_lambda_function" "worker" {
  function_name     = "${local.name}-worker"
  role              = aws_iam_role.api.arn
  runtime           = "python3.12"
  handler           = "agentconstruct.lambda_worker.handler"
  s3_bucket         = var.artifact_bucket
  s3_key            = var.artifact_key
  s3_object_version = var.artifact_object_version
  timeout           = 300
  memory_size       = 1024

  environment {
    variables = local.runtime_environment
  }
  tags = local.common_tags
}

resource "aws_lambda_event_source_mapping" "worker" {
  event_source_arn = aws_sqs_queue.worker.arn
  function_name    = aws_lambda_function.worker.arn
  batch_size       = 1

  depends_on = [aws_iam_role_policy.worker_queue]
}

resource "aws_cloudwatch_event_rule" "worker_tick" {
  name                = "${local.name}-worker-tick"
  schedule_expression = "rate(1 minute)"
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "worker_tick" {
  rule      = aws_cloudwatch_event_rule.worker_tick.name
  target_id = "worker-queue"
  arn       = aws_sqs_queue.worker.arn
}

resource "aws_sqs_queue_policy" "worker" {
  queue_url = aws_sqs_queue.worker.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.worker.arn
      Condition = { ArnEquals = { "aws:SourceArn" = aws_cloudwatch_event_rule.worker_tick.arn } }
    }]
  })
}

resource "aws_budgets_budget" "monthly" {
  name         = "${local.name}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = var.budget_notification_email == "" ? [] : [var.budget_notification_email]
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 80
      threshold_type             = "PERCENTAGE"
      notification_type          = "FORECASTED"
      subscriber_email_addresses = [notification.value]
    }
  }
}

check "no_network_egress_infrastructure" {
  assert {
    condition     = length(aws_subnet.database) == 2
    error_message = "Aurora requires exactly two isolated subnets. This stack must not add NAT or Internet Gateways."
  }
}
