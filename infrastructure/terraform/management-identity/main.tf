data "aws_caller_identity" "current" {}
locals {
  tags = { Project = "agentconstruct", ManagedBy = "terraform", Scope = "control-plane-identity", Purpose = "customer-discovery" }
  discovery_arns = [
    "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/agentconstruct-*-discovery",
    "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/AgentConstructDiscovery-*",
  ]
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
  tags            = local.tags
}

data "aws_iam_policy_document" "assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:ref:refs/heads/main"]
    }
  }
  dynamic "statement" {
    for_each = var.bootstrap_operator_principal_arn == null ? [] : [var.bootstrap_operator_principal_arn]
    content {
      sid     = "TemporaryCustomerOwnerVerification"
      effect  = "Allow"
      actions = ["sts:AssumeRole"]
      principals {
        type        = "AWS"
        identifiers = [statement.value]
      }
    }
  }
}

resource "aws_iam_role" "control_plane" {
  name                 = "agentconstruct-control-plane-github"
  description          = "GitHub OIDC control-plane identity. It can assume only AgentConstruct customer discovery roles."
  assume_role_policy   = data.aws_iam_policy_document.assume.json
  max_session_duration = 3600
  tags                 = local.tags
}
data "aws_iam_policy_document" "discover_customer" {
  statement {
    effect    = "Allow"
    actions   = ["sts:AssumeRole"]
    resources = local.discovery_arns
  }
}
resource "aws_iam_role_policy" "discover_customer" {
  name   = "agentconstruct-assume-customer-discovery"
  role   = aws_iam_role.control_plane.id
  policy = data.aws_iam_policy_document.discover_customer.json
}
