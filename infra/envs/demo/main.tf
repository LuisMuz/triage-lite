data "aws_caller_identity" "current" {}

locals {
  name_prefix       = "triagelite-${var.env}"
  metrics_namespace = "TriageLite"
}

module "storage" {
  source = "../../modules/storage"

  bucket_name   = "${local.name_prefix}-data-${data.aws_caller_identity.current.account_id}"
  table_name    = local.name_prefix
  force_destroy = true
}

module "functions" {
  source = "../../modules/functions"

  name_prefix       = local.name_prefix
  package_dir       = "${path.root}/../../../build/lambda"
  models_config     = file("${path.root}/../../../config/models.toml")
  bucket_name       = module.storage.bucket_name
  bucket_arn        = module.storage.bucket_arn
  table_name        = module.storage.table_name
  table_arn         = module.storage.table_arn
  metrics_namespace = local.metrics_namespace
}

module "pipeline" {
  source = "../../modules/pipeline"

  name_prefix   = local.name_prefix
  function_arns = module.functions.function_arns
  bucket_name   = module.storage.bucket_name
}

module "api" {
  source = "../../modules/api"

  name_prefix         = local.name_prefix
  function_name       = module.functions.function_names["api"]
  function_invoke_arn = module.functions.invoke_arns["api"]
}

module "observability" {
  source = "../../modules/observability"

  name_prefix       = local.name_prefix
  metrics_namespace = local.metrics_namespace
  function_names    = module.functions.function_names
  log_group_names   = module.functions.log_group_names
  state_machine_arn = module.pipeline.state_machine_arn
  alerts_topic_arn  = module.pipeline.alerts_topic_arn
  alert_email       = var.alert_email
}
