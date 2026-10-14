variable "region" {
  type        = string
  description = "AWS region for the customer workload pilot."
}

variable "expected_account_id" {
  type        = string
  description = "Account guard. Terraform fails if the caller is not in this AWS account."
}

variable "enable_service" {
  type        = bool
  description = "Create the App Runner service after the customer image has been pushed to ECR."
  default     = false
}

variable "image_identifier" {
  type        = string
  description = "Full ECR image URI with tag for the customer workload. Required when enable_service is true."
  default     = "placeholder.invalid/agentconstruct-customer-workload:unset"
}

variable "service_name" {
  type        = string
  description = "App Runner service name."
  default     = "agentconstruct-customer-control-plane"
}

variable "ecr_repository_name" {
  type        = string
  description = "ECR repository name for the customer workload image."
  default     = "agentconstruct-customer-ai-platform-control-plane"
}

variable "source_repository" {
  type        = string
  description = "Customer source repository URL used as pilot evidence."
  default     = "https://github.com/Bepoadewale/ai-platform-control-plane"
}

variable "source_commit" {
  type        = string
  description = "Customer source commit SHA used for the image build."
}

variable "plan_digest" {
  type        = string
  description = "AgentConstruct approved plan digest represented by this pilot execution."
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
