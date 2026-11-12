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

module "functions" {
  source = "../../modules/functions"

  name_prefix   = local.name_prefix
  package_dir   = "${path.root}/../../../build/lambda"
  models_config = file("${path.root}/../../../config/models.toml")
  bucket_name   = module.storage.bucket_name
  bucket_arn    = module.storage.bucket_arn
  table_name    = module.storage.table_name
  table_arn     = module.storage.table_arn
}

module "pipeline" {
  source = "../../modules/pipeline"

  name_prefix   = local.name_prefix
  function_arns = module.functions.function_arns
  bucket_name   = module.storage.bucket_name
}
