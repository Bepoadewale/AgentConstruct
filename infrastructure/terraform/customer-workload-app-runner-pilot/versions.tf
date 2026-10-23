terraform {
  required_version = ">= 1.9"

  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region

  assume_role {
    role_arn     = var.customer_execution_role_arn
    external_id  = var.customer_execution_external_id
    session_name = "davdeploy-customer-workload"
  }
}
