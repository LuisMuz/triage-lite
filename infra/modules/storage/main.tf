resource "aws_s3_bucket" "data" {
  #checkov:skip=CKV_AWS_18:Single-owner demo bucket; access logs would need a second bucket and nobody reviews them
  #checkov:skip=CKV_AWS_21:Stages overwrite by batch key and every object can be rebuilt from the input CSV
  #checkov:skip=CKV_AWS_144:Holds synthetic demo data that does not justify a replica in a second region
  #checkov:skip=CKV_AWS_145:SSE-S3 encrypts at rest; a KMS key adds about USD 1/month against an idle target under USD 3
  bucket        = var.bucket_name
  force_destroy = var.force_destroy
}

resource "aws_s3_bucket_ownership_controls" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    id     = "expire-work"
    status = "Enabled"

    filter {
      prefix = "work/"
    }

    expiration {
      days = var.work_retention_days
    }
  }

  rule {
    id     = "abort-incomplete-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = var.incomplete_upload_retention_days
    }
  }
}

resource "aws_s3_bucket_notification" "data" {
  bucket      = aws_s3_bucket.data.id
  eventbridge = true
}

data "aws_iam_policy_document" "data_tls_only" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]

    resources = [
      aws_s3_bucket.data.arn,
      "${aws_s3_bucket.data.arn}/*",
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "data" {
  bucket     = aws_s3_bucket.data.id
  policy     = data.aws_iam_policy_document.data_tls_only.json
  depends_on = [aws_s3_bucket_public_access_block.data]
}

resource "aws_dynamodb_table" "main" {
  #checkov:skip=CKV_AWS_28:Point-in-time recovery is off by design; the demo holds synthetic, reproducible data
  #checkov:skip=CKV_AWS_119:The AWS-owned key encrypts at rest for free; a customer-managed KMS key adds cost with no benefit here
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = false
  }
}
