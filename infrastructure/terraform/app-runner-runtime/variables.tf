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

variable "enable_durable_database" {
  type        = bool
  description = "Create private RDS PostgreSQL and wire App Runner to it. Required for production hosted mode."
  default     = false
}

variable "database_name" {
  type        = string
  description = "AgentConstruct control-plane PostgreSQL database name."
  default     = "agentconstruct"
}

variable "database_instance_class" {
  type        = string
  description = "RDS instance class for the hosted AgentConstruct control plane."
  default     = "db.t4g.micro"
}

variable "database_allocated_storage" {
  type        = number
  description = "Allocated RDS storage in GiB."
  default     = 20
}

variable "database_backup_retention_days" {
  type        = number
  description = "RDS automated backup retention in days."
  default     = 7
}

variable "database_deletion_protection" {
  type        = bool
  description = "Enable deletion protection for the production control-plane database."
  default     = true
}

variable "runtime_vpc_cidr" {
  type        = string
  description = "CIDR block for the optional hosted runtime VPC."
  default     = "10.42.0.0/16"
}
