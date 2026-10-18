variable "region" {
  type        = string
  description = "AWS region used by the AgentConstruct control plane."
  default     = "us-east-1"
}

variable "github_oidc_repository_subject" {
  type        = string
  description = "Immutable GitHub OIDC repository subject prefix configured for this repository."
  default     = "repo:Bepoadewale@99020860/AgentConstruct@1391292548"
}

variable "state_bucket_name" {
  type        = string
  description = "Existing private Terraform state bucket."
  default     = "agentconstruct-tfstate-654654474502"
}

variable "lock_table_name" {
  type        = string
  description = "Existing Terraform state lock table."
  default     = "agentconstruct-terraform-locks"
}

variable "plan_retention_days" {
  type        = number
  description = "Days to retain encrypted saved plans and manifests."
  default     = 30
}

variable "release_retention_days" {
  type        = number
  description = "Days to retain immutable Lambda release packages."
  default     = 90
}
