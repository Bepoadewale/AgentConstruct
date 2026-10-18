variable "region" { type = string }
variable "oidc_provider_arn" {
  type        = string
  description = "OIDC provider ARN for the davdeploy runtime cluster; not GitHub Actions."
}
variable "oidc_issuer_hostpath" {
  type        = string
  description = "OIDC issuer without https://, used only in the IRSA trust conditions."
}
variable "namespace" {
  type    = string
  default = "davdeploy"
}
variable "service_account" {
  type    = string
  default = "control-plane"
}
variable "secret_arn_prefix" {
  type        = string
  description = "Secrets Manager ARN prefix for per-customer ExternalIds, ending with *."
}
