data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_partition" "current" {}

locals {
  account   = data.aws_caller_identity.current.account_id
  region    = data.aws_region.current.region
  partition = data.aws_partition.current.partition

  functions = {
    normalize      = { memory = 512, timeout = 60 }
    classify_chunk = { memory = 512, timeout = 300 }
    dedupe         = { memory = 1024, timeout = 600 }
    summarize      = { memory = 512, timeout = 180 }
    finalize       = { memory = 512, timeout = 60 }
  }

  stage_sections = {
    for stage in ["classify", "dedupe_judge", "summarize"] :
    stage => one(regexall("(?ms)^\\[stages\\.${stage}\\]$(.*?)(?:^\\[|\\z)", var.models_config))[0]
  }
  stage_models = {
    for stage, section in local.stage_sections :
    stage => one(regexall("(?m)^model_id = \"([^\"]+)\"", section))[0]
  }
  embedding_model = one(regexall(
    "(?m)^model_id = \"([^\"]+)\"",
    one(regexall("(?ms)^\\[embedding\\]$(.*?)(?:^\\[|\\z)", var.models_config))[0],
  ))[0]

  claude_profile_for = {
    classify_chunk = local.stage_models["classify"]
    dedupe         = local.stage_models["dedupe_judge"]
    summarize      = local.stage_models["summarize"]
  }

  objects = "${var.bucket_arn}/"
}

resource "aws_lambda_layer_version" "dependencies" {
  layer_name               = "${var.name_prefix}-dependencies"
  filename                 = "${var.package_dir}/layer.zip"
  source_code_hash         = filebase64sha256("${var.package_dir}/layer.zip")
  compatible_runtimes      = ["python3.12"]
  compatible_architectures = ["arm64"]
}

resource "aws_cloudwatch_log_group" "function" {
  #checkov:skip=CKV_AWS_158:Logs hold IDs, counts and scrubbed metadata only; a customer-managed KMS key adds cost without protecting anything sensitive
  #checkov:skip=CKV_AWS_338:Fourteen days is enough to debug a demo run and keeps storage near zero
  for_each = local.functions

  name              = "/aws/lambda/${var.name_prefix}-${each.key}"
  retention_in_days = var.log_retention_days
}

data "aws_iam_policy_document" "assume_lambda" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "function" {
  for_each = local.functions

  name               = "${var.name_prefix}-${each.key}"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}

resource "aws_lambda_function" "function" {
  #checkov:skip=CKV_AWS_50:Tracing waits for the observability work; structured logs carry batch_id and call_id meanwhile
  #checkov:skip=CKV_AWS_115:Step Functions caps the fan-out; reserving concurrency would eat into a small new-account quota
  #checkov:skip=CKV_AWS_116:Step Functions invokes synchronously and handles failures, so a dead-letter queue would never receive anything
  #checkov:skip=CKV_AWS_117:No VPC by design (TL-01); the functions only call AWS APIs, and a VPC would need NAT or endpoints
  #checkov:skip=CKV_AWS_173:Environment variables hold resource names only, never secrets
  #checkov:skip=CKV_AWS_272:Single-owner project; code comes from make build on the owner's machine, not a third party
  for_each = local.functions

  function_name    = "${var.name_prefix}-${each.key}"
  role             = aws_iam_role.function[each.key].arn
  handler          = "triagelite.handlers.${each.key}.handler"
  runtime          = "python3.12"
  architectures    = ["arm64"]
  memory_size      = each.value.memory
  timeout          = each.value.timeout
  filename         = "${var.package_dir}/code.zip"
  source_code_hash = filebase64sha256("${var.package_dir}/code.zip")
  layers           = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      TRIAGELITE_DATA_BUCKET = var.bucket_name
      TRIAGELITE_TABLE_NAME  = var.table_name
      TRIAGELITE_AWS_REGION  = local.region
      TRIAGELITE_LOG_LEVEL   = var.log_level
      OPENBLAS_CORETYPE      = "NEOVERSEN1"
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.function[each.key].name
  }

  depends_on = [aws_iam_role_policy.function]
}
