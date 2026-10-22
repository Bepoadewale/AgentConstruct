locals {
  prefix = "${var.project}-${var.customer_connection_id}"
  tags = {
    Project              = var.project
    ManagedBy            = "terraform"
    Scope                = "customer-connection"
    CustomerConnectionId = var.customer_connection_id
    Purpose              = "identity-only"
  }
}

data "aws_iam_policy_document" "assume_davdeploy" {
  statement {
    sid     = "AllowOnlydavdeployControlPlaneWithExternalId"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = [var.davdeploy_control_plane_role_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = [var.external_id]
    }
  }
}

resource "aws_iam_role" "discovery" {
  name                 = "${local.prefix}-discovery"
  description          = "davdeploy customer inventory and cost discovery only; no mutation permissions."
  assume_role_policy   = data.aws_iam_policy_document.assume_davdeploy.json
  max_session_duration = 3600
  tags                 = merge(local.tags, { Access = "discovery-read-only" })
}

data "aws_iam_policy_document" "discovery" {
  statement {
    sid    = "DiscoverApprovedInfrastructure"
    effect = "Allow"
    actions = [
      "apprunner:ListServices",
      "apprunner:DescribeService",
      "ce:GetCostAndUsage",
      "ce:GetCostForecast",
      "ce:GetDimensionValues",
      "ec2:Describe*",
      "ecr:DescribeRepositories",
      "ecr:ListImages",
      "ecs:DescribeClusters",
      "ecs:DescribeServices",
      "ecs:ListClusters",
      "ecs:ListServices",
      "eks:DescribeCluster",
      "eks:ListClusters",
      "elasticache:Describe*",
      "lambda:GetFunctionConfiguration",
      "lambda:ListFunctions",
      "pricing:GetProducts",
      "rds:Describe*",
      "resource-groups:GetResources",
      "s3:GetBucketLocation",
      "s3:GetBucketTagging",
      "s3:ListAllMyBuckets",
      "tag:GetResources"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "discovery" {
  name   = "${local.prefix}-discovery"
  role   = aws_iam_role.discovery.id
  policy = data.aws_iam_policy_document.discovery.json
}

resource "aws_iam_role" "execution_contract" {
  name                 = "${local.prefix}-execution"
  description          = "Reserved davdeploy execution role. It has no permissions until a separately approved profile-specific policy is attached."
  assume_role_policy   = data.aws_iam_policy_document.assume_davdeploy.json
  max_session_duration = 3600
  tags                 = merge(local.tags, { Access = "no-permissions-contract" })
}
