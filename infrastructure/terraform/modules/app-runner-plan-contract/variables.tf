variable "project_id" {
  type        = string
  description = "AgentConstruct project ID that owns the approved customer plan."
}

variable "revision_id" {
  type        = string
  description = "Approved customer-plan revision ID."
}

variable "source_deployment_plan_id" {
  type        = string
  description = "Internal immutable deployment-plan contract that produced this customer review."
}

variable "plan_digest" {
  type        = string
  description = "SHA-256 digest of the exact approved customer-plan revision."

  validation {
    condition     = can(regex("^[a-f0-9]{64}$", var.plan_digest))
    error_message = "plan_digest must be a lowercase 64-character SHA-256 hex digest."
  }
}

variable "profile" {
  type        = string
  description = "Selected architecture profile. This module is only valid for App Runner."

  validation {
    condition     = var.profile == "aws-app-runner"
    error_message = "The App Runner plan contract only accepts profile aws-app-runner."
  }
}

variable "service_name" {
  type        = string
  description = "Plan-only App Runner service name preview."

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,62}$", var.service_name))
    error_message = "service_name must be lowercase alphanumeric or hyphenated."
  }
}

variable "repository_url" {
  type        = string
  description = "Selected GitHub repository URL from the approved plan."
}

variable "repository_branch" {
  type        = string
  description = "Selected GitHub branch from the approved plan."
}

variable "aws_account_id" {
  type        = string
  description = "Selected customer AWS account ID, or a placeholder when still fixture-only."
}

variable "aws_region" {
  type        = string
  description = "Selected AWS region."

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "aws_region must look like us-east-1."
  }
}

variable "source_boundary" {
  type        = string
  description = "Human-readable source/ECR boundary. This plan-only contract never builds or pushes images."
}

variable "image_repository" {
  type        = string
  description = "Expected immutable image repository boundary for a future reviewed build."
}

variable "environment_variables" {
  type        = map(string)
  description = "Non-secret environment variables derived from the approved plan."
}

variable "secret_references" {
  type        = map(string)
  description = "Secret reference names/ARN-like placeholders. Secret values are never rendered."
}

variable "https_access" {
  type = object({
    ingress               = string
    custom_domain         = string
    private_data_boundary = string
  })
  description = "HTTPS/access assumptions for the App Runner profile."
}

variable "iam" {
  type = object({
    runtime_role    = string
    deployment_role = string
  })
  description = "IAM boundaries for runtime and future explicit deployment."
}

variable "observability" {
  type = object({
    metrics_backend    = string
    grafana            = string
    scrape_targets     = list(string)
    baseline_dashboard = any
    access_boundary    = string
    limitations        = list(string)
    cost_assumption    = string
  })
  description = "Mandatory Prometheus/Grafana monitoring contract."
}

variable "tags" {
  type        = map(string)
  description = "Required ownership, plan-digest and project tags."
}
