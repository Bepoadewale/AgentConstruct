variable "region" {
  type        = string
  description = "AWS region for the AgentConstruct control plane."
  default     = "us-east-1"
}

variable "frontend_origin" {
  type        = string
  description = "Exact HTTPS Cloudflare Pages or custom-domain origin."

  validation {
    condition     = can(regex("^https://[^/]+$", var.frontend_origin))
    error_message = "frontend_origin must be one exact HTTPS origin without a trailing slash."
  }
}

variable "artifact_bucket" {
  type        = string
  description = "Existing private S3 bucket containing the verified Lambda package."
}

variable "artifact_key" {
  type        = string
  description = "Versioned S3 key for the verified Lambda zip package."
}

variable "artifact_object_version" {
  type        = string
  description = "Optional immutable S3 object version for the Lambda package."
  default     = null
}

variable "cognito_domain_prefix" {
  type        = string
  description = "Globally unique Cognito managed-login domain prefix."
}

variable "google_identity_provider_enabled" {
  type        = bool
  description = "Expose Google after the provider is configured outside Terraform state."
  default     = false
}

variable "ses_identity_arn" {
  type        = string
  description = "Verified SES identity ARN for production OTP email. Empty uses Cognito default email delivery."
  default     = ""
}

variable "ses_from_address" {
  type        = string
  description = "Verified From address used when ses_identity_arn is set."
  default     = ""
}

variable "database_name" {
  type        = string
  description = "Aurora PostgreSQL database name."
  default     = "agentconstruct"
}

variable "aurora_engine_version" {
  type        = string
  description = "Aurora PostgreSQL version approved for Data API and Serverless v2."
  default     = "16.6"
}

variable "aurora_min_capacity" {
  type        = number
  description = "Minimum Aurora capacity units."
  default     = 0
}

variable "aurora_seconds_until_auto_pause" {
  type        = number
  description = "Idle time before Aurora scales to zero when the selected engine supports auto-pause."
  default     = 900
}

variable "aurora_max_capacity" {
  type        = number
  description = "Maximum Aurora capacity units."
  default     = 2
}

variable "database_deletion_protection" {
  type        = bool
  description = "Protect the control-plane database from accidental deletion."
  default     = true
}

variable "monthly_budget_usd" {
  type        = number
  description = "Alerting threshold only. It does not automatically stop resources."
  default     = 50
}

variable "budget_notification_email" {
  type        = string
  description = "Optional operator email for budget alerts."
  default     = ""
  sensitive   = true
}

variable "nova_model_id" {
  type        = string
  description = "Amazon Nova 2 Lite inference profile."
  default     = "us.amazon.nova-2-lite-v1:0"
}
