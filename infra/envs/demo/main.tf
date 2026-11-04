data "aws_caller_identity" "current" {}

locals {
  name_prefix = "triagelite-${var.env}"
}

module "storage" {
  source = "../../modules/storage"

  bucket_name   = "${local.name_prefix}-data-${data.aws_caller_identity.current.account_id}"
  table_name    = local.name_prefix
  force_destroy = true
}
