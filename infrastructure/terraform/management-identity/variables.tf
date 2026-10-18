variable "region" { type = string }
variable "github_repository" {
  type    = string
  default = "Bepoadewale/davdeploy"
}
variable "bootstrap_operator_principal_arn" {
  type        = string
  default     = null
  nullable    = true
  description = "Temporary customer-owner principal allowed only for local role-chain verification. Leave null after proof."
}
