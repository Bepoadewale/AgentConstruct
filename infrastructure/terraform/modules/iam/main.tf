variable "name" { type = string }
variable "oidc_issuer" { type = string }
variable "oidc_provider_arn" { type = string }
variable "namespace" { type = string }
variable "service_account" { type = string }
variable "tags" { type = map(string) }
variable "secret_arns" { type = list(string) }

data "aws_iam_policy_document" "assume_irsa" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${trimprefix(var.oidc_issuer, "https://")}:sub"
      values   = ["system:serviceaccount:${var.namespace}:${var.service_account}"]
    }
  }
}
resource "aws_iam_role" "workload" {
  name               = "${var.name}-workload"
  assume_role_policy = data.aws_iam_policy_document.assume_irsa.json
  tags               = var.tags
}
data "aws_iam_policy_document" "workload" {
  statement {
    sid       = "ReadOnlyApprovedSecrets"
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = var.secret_arns
  }
}
resource "aws_iam_role_policy" "workload" {
  name   = "read-approved-secrets"
  role   = aws_iam_role.workload.id
  policy = data.aws_iam_policy_document.workload.json
}
output "workload_role_arn" { value = aws_iam_role.workload.arn }
