variable "region" {
  type        = string
  description = "AWS region for the hosted AgentConstruct runtime."
}

variable "enable_service" {
  type        = bool
  description = "Create the App Runner service only after the image has been pushed to ECR."
  default     = false
}

variable "image_identifier" {
  type        = string
  description = "Full ECR image URI with tag for the AgentConstruct runtime. Required when enable_service is true."
  default     = "placeholder.invalid/agentconstruct:unset"
}

variable "customer_template_url" {
  type        = string
  description = "Public, versioned CloudFormation template URL used for customer read-only discovery onboarding."
}

variable "connection_secret_prefix" {
  type        = string
  description = "Secrets Manager prefix for per-connection ExternalIds."
  default     = "agentconstruct/customer-connections"
}

variable "cpu" {
  type        = string
  description = "App Runner CPU size."
  default     = "256"
}

variable "memory" {
  type        = string
  description = "App Runner memory size."
  default     = "512"
}
