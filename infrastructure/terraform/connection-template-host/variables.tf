variable "region" {
  type        = string
  description = "AWS region for the public CloudFormation-template bucket."
}

variable "bucket_name" {
  type        = string
  description = "Globally unique bucket name. This bucket serves only public, non-secret CloudFormation templates."
}
