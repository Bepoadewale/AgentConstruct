locals {
  template_source = "${path.module}/../../cloudformation/customer-discovery-role.yaml"
  template_hash   = filesha256(local.template_source)
  template_key    = "cloudformation/customer-discovery-role-${local.template_hash}.yaml"
  tags = {
    Project   = "agentconstruct"
    ManagedBy = "terraform"
    Purpose   = "public-cloudformation-template-only"
  }
}

resource "aws_s3_bucket" "templates" {
  bucket = var.bucket_name
  tags   = local.tags
}

resource "aws_s3_bucket_ownership_controls" "templates" {
  bucket = aws_s3_bucket.templates.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "templates" {
  bucket = aws_s3_bucket.templates.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "templates" {
  bucket = aws_s3_bucket.templates.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "templates" {
  bucket                  = aws_s3_bucket.templates.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = false
  restrict_public_buckets = false
}

data "aws_iam_policy_document" "public_template_only" {
  statement {
    sid       = "PublicReadOnlyForVersionedCloudFormationTemplates"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.templates.arn}/cloudformation/*"]
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "templates" {
  bucket     = aws_s3_bucket.templates.id
  policy     = data.aws_iam_policy_document.public_template_only.json
  depends_on = [aws_s3_bucket_public_access_block.templates]
}

resource "aws_s3_object" "customer_discovery_role" {
  bucket       = aws_s3_bucket.templates.id
  key          = local.template_key
  source       = local.template_source
  etag         = filemd5(local.template_source)
  content_type = "application/x-yaml"
  tags         = local.tags
  depends_on = [
    aws_s3_bucket_ownership_controls.templates,
    aws_s3_bucket_server_side_encryption_configuration.templates,
    aws_s3_bucket_versioning.templates,
  ]
}
