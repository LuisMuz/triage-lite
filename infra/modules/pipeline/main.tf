data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_partition" "current" {}

locals {
  account   = data.aws_caller_identity.current.account_id
  region    = data.aws_region.current.region
  partition = data.aws_partition.current.partition

  state_machine_name = "${var.name_prefix}-pipeline"
  state_machine_arn  = "arn:${local.partition}:states:${local.region}:${local.account}:stateMachine:${local.state_machine_name}"
  rule_name          = "${var.name_prefix}-csv-uploaded"

  lambda_errors = [
    "Lambda.ServiceException",
    "Lambda.AWSLambdaException",
    "Lambda.SdkClientException",
    "Lambda.TooManyRequestsException",
  ]
  model_errors = ["LLMRateLimitError", "LLMTransientError"]

  lambda_retry = [{
    ErrorEquals     = local.lambda_errors
    IntervalSeconds = 2
    BackoffRate     = 2
    MaxAttempts     = 3
    JitterStrategy  = "FULL"
  }]
  model_retry = [{
    ErrorEquals     = concat(local.model_errors, local.lambda_errors)
    IntervalSeconds = 2
    BackoffRate     = 2
    MaxAttempts     = 4
    JitterStrategy  = "FULL"
  }]
  notify_retry = [{
    ErrorEquals     = ["States.TaskFailed"]
    IntervalSeconds = 2
    BackoffRate     = 2
    MaxAttempts     = 2
    JitterStrategy  = "FULL"
  }]

  definition = templatefile("${path.module}/statemachine.asl.json", {
    partition             = local.partition
    functions             = var.function_arns
    topic_arn             = aws_sns_topic.alerts.arn
    timeout_seconds       = var.execution_timeout_seconds
    max_chunk_concurrency = var.max_chunk_concurrency
    lambda_retry          = jsonencode(local.lambda_retry)
    model_retry           = jsonencode(local.model_retry)
    notify_retry          = jsonencode(local.notify_retry)
  })
}

resource "aws_sns_topic" "alerts" {
  #checkov:skip=CKV_AWS_26:Messages carry IDs and error class names only; CloudWatch alarms cannot publish to the AWS-managed SNS key, and a customer-managed key costs $1 a month
  name = "${var.name_prefix}-alerts"
}

resource "aws_sfn_state_machine" "pipeline" {
  #checkov:skip=CKV_AWS_284:Tracing waits for the observability work, like the functions
  #checkov:skip=CKV_AWS_285:Standard workflows keep 90 days of execution history; CloudWatch log delivery needs a Resource "*" policy and could carry error causes that quote incident text
  name       = local.state_machine_name
  type       = "STANDARD"
  role_arn   = aws_iam_role.state_machine.arn
  definition = local.definition

  depends_on = [aws_iam_role_policy.state_machine]
}

resource "aws_cloudwatch_event_rule" "csv_uploaded" {
  name        = local.rule_name
  description = "A CSV landed in incoming/ of the data bucket."
  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = { name = [var.bucket_name] }
      object = { key = [{ wildcard = "${var.upload_prefix}*.csv" }] }
    }
  })
}

resource "aws_cloudwatch_event_target" "start_pipeline" {
  rule     = aws_cloudwatch_event_rule.csv_uploaded.name
  arn      = aws_sfn_state_machine.pipeline.arn
  role_arn = aws_iam_role.events.arn

  input_transformer {
    input_paths    = { key = "$.detail.object.key" }
    input_template = "{\"source_key\": <key>}"
  }

  retry_policy {
    maximum_event_age_in_seconds = 3600
    maximum_retry_attempts       = 10
  }
}
