data "aws_iam_policy_document" "assume_states" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [local.state_machine_arn]
    }
  }
}

resource "aws_iam_role" "state_machine" {
  name               = "${var.name_prefix}-pipeline"
  assume_role_policy = data.aws_iam_policy_document.assume_states.json
}

data "aws_iam_policy_document" "state_machine" {
  statement {
    sid       = "InvokeStages"
    actions   = ["lambda:InvokeFunction"]
    resources = flatten([for stage in local.stages : [var.function_arns[stage], "${var.function_arns[stage]}:*"]])
  }

  statement {
    sid       = "PublishFailures"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.alerts.arn]
  }
}

resource "aws_iam_role_policy" "state_machine" {
  name   = "${var.name_prefix}-pipeline"
  role   = aws_iam_role.state_machine.id
  policy = data.aws_iam_policy_document.state_machine.json
}

data "aws_iam_policy_document" "assume_events" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_cloudwatch_event_rule.csv_uploaded.arn]
    }
  }
}

resource "aws_iam_role" "events" {
  name               = "${var.name_prefix}-start-pipeline"
  assume_role_policy = data.aws_iam_policy_document.assume_events.json
}

data "aws_iam_policy_document" "events" {
  statement {
    sid       = "StartPipeline"
    actions   = ["states:StartExecution"]
    resources = [aws_sfn_state_machine.pipeline.arn]
  }
}

resource "aws_iam_role_policy" "events" {
  name   = "${var.name_prefix}-start-pipeline"
  role   = aws_iam_role.events.id
  policy = data.aws_iam_policy_document.events.json
}
