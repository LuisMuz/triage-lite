data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_partition" "current" {}

locals {
  account   = data.aws_caller_identity.current.account_id
  region    = data.aws_region.current.region
  partition = data.aws_partition.current.partition

  dashboard_name   = var.name_prefix
  model_functions  = ["classify_chunk", "dedupe", "summarize"]
  model_log_groups = [for function in local.model_functions : var.log_group_names[function]]
  sources          = join(" | ", [for group in local.model_log_groups : "SOURCE '${group}'"])

  queries = {
    slowest-llm-calls            = <<-EOT
      fields @timestamp, batch_id, stage, model_id, prompt_version, attempt, status, latency_ms, input_tokens, output_tokens
      | filter message = "llm_call"
      | sort latency_ms desc
      | limit 20
    EOT
    validation-failures-by-stage = <<-EOT
      filter message = "llm_call" and status = "validation_error"
      | stats count(*) as failures by stage, prompt_version
      | sort failures desc
    EOT
    cost-by-batch                = <<-EOT
      filter message = "llm_call"
      | stats sum(cost_usd) as cost_usd, count(*) as calls, sum(input_tokens) as input_tokens, sum(output_tokens) as output_tokens, min(@timestamp) as first_call by batch_id
      | sort first_call desc
      | limit 20
    EOT
  }
  tokens_by_stage = <<-EOT
    filter message = "llm_call"
    | stats sum(input_tokens) as input_tokens, sum(output_tokens) as output_tokens by stage
  EOT

  custom = var.metrics_namespace
  states = "AWS/States"
  lambda = "AWS/Lambda"

  log_widget = { for name, query in merge(local.queries, { tokens-by-stage = local.tokens_by_stage }) :
    name => {
      region = local.region
      query  = "${local.sources} | ${trimspace(query)}"
    }
  }

  widgets = [
    {
      type = "log", x = 0, y = 0, width = 12, height = 6
      properties = merge(local.log_widget["cost-by-batch"], {
        title = "Cost per batch (USD)", view = "table"
      })
    },
    {
      type = "metric", x = 12, y = 0, width = 12, height = 6
      properties = {
        title   = "Model cost per hour (USD)", region = local.region, view = "timeSeries"
        period  = 3600, stat = "Sum"
        metrics = [[local.custom, "CostUSD", { label = "CostUSD" }]]
      }
    },
    {
      type = "log", x = 0, y = 6, width = 12, height = 6
      properties = merge(local.log_widget["tokens-by-stage"], {
        title = "Tokens by stage", view = "bar"
      })
    },
    {
      type = "metric", x = 12, y = 6, width = 12, height = 6
      properties = {
        title  = "Tokens per hour", region = local.region, view = "timeSeries", stacked = true
        period = 3600, stat = "Sum"
        metrics = [
          [local.custom, "InputTokens"],
          [local.custom, "OutputTokens"],
        ]
      }
    },
    {
      type = "metric", x = 0, y = 12, width = 12, height = 6
      properties = {
        title = "Validation errors, manual incidents and PII redactions", region = local.region
        view  = "timeSeries", period = 3600, stat = "Sum"
        metrics = [
          [local.custom, "ValidationErrors"],
          [local.custom, "NeedsManual"],
          [local.custom, "PIIRedactions"],
        ]
      }
    },
    {
      type = "metric", x = 12, y = 12, width = 12, height = 6
      properties = {
        title = "Model call latency (ms)", region = local.region, view = "timeSeries", period = 3600
        metrics = [
          [local.custom, "LatencyMs", { stat = "p50", label = "p50" }],
          [local.custom, "LatencyMs", { stat = "p95", label = "p95" }],
          [local.custom, "LatencyMs", { stat = "Maximum", label = "max" }],
        ]
      }
    },
    {
      type = "metric", x = 0, y = 18, width = 8, height = 6
      properties = {
        title = "Pipeline runs", region = local.region, view = "timeSeries", period = 300, stat = "Sum"
        metrics = [
          for metric in ["ExecutionsStarted", "ExecutionsSucceeded", "ExecutionsFailed", "ExecutionsTimedOut"] :
          [local.states, metric, "StateMachineArn", var.state_machine_arn]
        ]
      }
    },
    {
      type = "metric", x = 8, y = 18, width = 8, height = 6
      properties = {
        title = "Function errors", region = local.region, view = "timeSeries", period = 300, stat = "Sum"
        metrics = [
          for key, name in var.function_names :
          [local.lambda, "Errors", "FunctionName", name, { label = key }]
        ]
      }
    },
    {
      type = "metric", x = 16, y = 18, width = 8, height = 6
      properties = {
        title = "Function throttles", region = local.region, view = "timeSeries", period = 300, stat = "Sum"
        metrics = [
          for key, name in var.function_names :
          [local.lambda, "Throttles", "FunctionName", name, { label = key }]
        ]
      }
    },
    {
      type = "log", x = 0, y = 24, width = 12, height = 6
      properties = merge(local.log_widget["validation-failures-by-stage"], {
        title = "Validation failures by stage", view = "table"
      })
    },
    {
      type = "log", x = 12, y = 24, width = 12, height = 6
      properties = merge(local.log_widget["slowest-llm-calls"], {
        title = "Slowest model calls", view = "table"
      })
    },
  ]
}

resource "aws_cloudwatch_dashboard" "pipeline" {
  dashboard_name = local.dashboard_name
  dashboard_body = jsonencode({ widgets = local.widgets })
}

resource "aws_cloudwatch_query_definition" "saved" {
  for_each = local.queries

  name            = "${var.name_prefix}/${each.key}"
  log_group_names = local.model_log_groups
  query_string    = trimspace(each.value)
}

resource "aws_cloudwatch_metric_alarm" "run_failed" {
  alarm_name          = "${var.name_prefix}-run-failed"
  alarm_description   = "A pipeline run failed or timed out. A timed-out run never reaches MarkFailed, so this alarm is its only signal."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 1
  treat_missing_data  = "notBreaching"
  alarm_actions       = [var.alerts_topic_arn]

  metric_query {
    id          = "stopped"
    expression  = "SUM([failed, timed_out])"
    label       = "Failed or timed-out runs"
    return_data = true
  }

  metric_query {
    id = "failed"

    metric {
      namespace   = local.states
      metric_name = "ExecutionsFailed"
      period      = 300
      stat        = "Sum"
      dimensions  = { StateMachineArn = var.state_machine_arn }
    }
  }

  metric_query {
    id = "timed_out"

    metric {
      namespace   = local.states
      metric_name = "ExecutionsTimedOut"
      period      = 300
      stat        = "Sum"
      dimensions  = { StateMachineArn = var.state_machine_arn }
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "function_errors" {
  alarm_name          = "${var.name_prefix}-function-errors"
  alarm_description   = "Functions raised ${var.lambda_errors_alarm} or more errors within 5 minutes, counting attempts Step Functions retried."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = var.lambda_errors_alarm
  treat_missing_data  = "notBreaching"
  alarm_actions       = [var.alerts_topic_arn]

  metric_query {
    id          = "errors"
    expression  = "SUM([${join(", ", [for key in keys(var.function_names) : "e_${key}"])}])"
    label       = "Errors, all functions"
    return_data = true
  }

  dynamic "metric_query" {
    for_each = var.function_names

    content {
      id = "e_${metric_query.key}"

      metric {
        namespace   = local.lambda
        metric_name = "Errors"
        period      = 300
        stat        = "Sum"
        dimensions  = { FunctionName = metric_query.value }
      }
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "daily_cost" {
  alarm_name          = "${var.name_prefix}-daily-model-cost"
  alarm_description   = "Model calls cost ${var.daily_cost_alarm_usd} USD or more over the last 24 hours, as priced by config/pricing.toml."
  namespace           = local.custom
  metric_name         = "CostUSD"
  statistic           = "Sum"
  period              = 86400
  evaluation_periods  = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = var.daily_cost_alarm_usd
  treat_missing_data  = "notBreaching"
  alarm_actions       = [var.alerts_topic_arn]
}

data "aws_iam_policy_document" "alerts" {
  statement {
    sid       = "AlarmsPublish"
    actions   = ["sns:Publish"]
    resources = [var.alerts_topic_arn]

    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:${local.partition}:cloudwatch:${local.region}:${local.account}:alarm:${var.name_prefix}-*"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account]
    }
  }
}

resource "aws_sns_topic_policy" "alerts" {
  arn    = var.alerts_topic_arn
  policy = data.aws_iam_policy_document.alerts.json
}

resource "aws_sns_topic_subscription" "email" {
  count = nonsensitive(var.alert_email != null) ? 1 : 0

  topic_arn = var.alerts_topic_arn
  protocol  = "email"
  endpoint  = var.alert_email
}
