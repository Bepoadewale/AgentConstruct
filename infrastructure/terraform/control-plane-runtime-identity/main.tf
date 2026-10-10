data "aws_caller_identity" "current" {}

locals {
  tags = {
    Project   = "agentconstruct"
    ManagedBy = "terraform"
    Scope     = "control-plane-runtime"
    Purpose   = "read-only-customer-discovery"
  }
}

data "aws_iam_policy_document" "runtime_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${var.oidc_issuer_hostpath}:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "${var.oidc_issuer_hostpath}:sub"
      values   = ["system:serviceaccount:${var.namespace}:${var.service_account}"]
    }
  }
}

resource "aws_iam_role" "runtime" {
  name                 = "agentconstruct-control-plane-runtime"
  description          = "Runtime-only identity. It may assume customer discovery roles and read per-connection secrets."
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
    sid       = "ReadOnlyConnectionExternalIds"
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [var.secret_arn_prefix]
  }
}

resource "aws_iam_role_policy" "runtime_permissions" {
  name   = "agentconstruct-runtime-customer-discovery"
  role   = aws_iam_role.runtime.id
  policy = data.aws_iam_policy_document.runtime_permissions.json
}
