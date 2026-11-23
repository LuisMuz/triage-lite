data "aws_iam_policy_document" "logs" {
  for_each = local.functions

  statement {
    sid       = "WriteOwnLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.function[each.key].arn}:*"]
  }
}

module "claude" {
  source   = "../bedrock_invoke"
  for_each = local.claude_profile_for

  profile_ids = [each.value]
}

data "aws_iam_policy_document" "normalize" {
  source_policy_documents = [data.aws_iam_policy_document.logs["normalize"].json]

  statement {
    sid       = "ReadUploads"
    actions   = ["s3:GetObject"]
    resources = ["${local.objects}incoming/*"]
  }

  statement {
    sid       = "WriteBatchAndChunks"
    actions   = ["s3:PutObject"]
    resources = ["${local.objects}work/*/normalized.json", "${local.objects}work/*/chunks/*"]
  }

  statement {
    sid       = "StartOrFailBatch"
    actions   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:BatchWriteItem"]
    resources = [var.table_arn]
  }
}

data "aws_iam_policy_document" "classify_chunk" {
  source_policy_documents = [
    data.aws_iam_policy_document.logs["classify_chunk"].json,
    module.claude["classify_chunk"].policy_json,
  ]

  statement {
    sid       = "ReadChunks"
    actions   = ["s3:GetObject"]
    resources = ["${local.objects}work/*/chunks/*"]
  }

  statement {
    sid       = "WriteResultsAndCalls"
    actions   = ["s3:PutObject"]
    resources = ["${local.objects}work/*/classified/*", "${local.objects}work/*/calls/classify-*"]
  }
}

data "aws_iam_policy_document" "dedupe" {
  source_policy_documents = [
    data.aws_iam_policy_document.logs["dedupe"].json,
    module.claude["dedupe"].policy_json,
  ]

  statement {
    sid       = "EmbedIncidents"
    actions   = ["bedrock:InvokeModel"]
    resources = ["arn:${local.partition}:bedrock:${local.region}::foundation-model/${local.embedding_model}"]
  }

  statement {
    sid       = "ReadBatch"
    actions   = ["s3:GetObject"]
    resources = ["${local.objects}work/*/normalized.json"]
  }

  statement {
    sid       = "WriteClustersAndCalls"
    actions   = ["s3:PutObject"]
    resources = ["${local.objects}work/*/dedupe.json", "${local.objects}work/*/calls/dedupe.jsonl"]
  }
}

data "aws_iam_policy_document" "summarize" {
  source_policy_documents = [
    data.aws_iam_policy_document.logs["summarize"].json,
    module.claude["summarize"].policy_json,
  ]

  statement {
    sid     = "ReadStageOutputs"
    actions = ["s3:GetObject"]
    resources = [
      "${local.objects}work/*/normalized.json",
      "${local.objects}work/*/dedupe.json",
      "${local.objects}work/*/classified/*",
    ]
  }

  statement {
    sid       = "TellMissingFromForbidden"
    actions   = ["s3:ListBucket"]
    resources = [var.bucket_arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["work/*"]
    }
  }

  statement {
    sid     = "WriteReports"
    actions = ["s3:PutObject"]
    resources = [
      "${local.objects}work/*/report_facts.json",
      "${local.objects}work/*/report_drafts.jsonl",
      "${local.objects}work/*/calls/summarize.jsonl",
      "${local.objects}reports/*",
    ]
  }
}

data "aws_iam_policy_document" "finalize" {
  source_policy_documents = [data.aws_iam_policy_document.logs["finalize"].json]

  statement {
    sid     = "ReadStageOutputs"
    actions = ["s3:GetObject"]
    resources = [
      "${local.objects}work/*/normalized.json",
      "${local.objects}work/*/dedupe.json",
      "${local.objects}work/*/report_drafts.jsonl",
      "${local.objects}work/*/classified/*",
      "${local.objects}work/*/calls/*",
    ]
  }

  statement {
    sid       = "TellMissingFromForbidden"
    actions   = ["s3:ListBucket"]
    resources = [var.bucket_arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["work/*"]
    }
  }

  statement {
    sid       = "WriteSummary"
    actions   = ["s3:PutObject"]
    resources = ["${local.objects}work/*/summary.json"]
  }

  statement {
    sid = "PublishBatch"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:BatchWriteItem",
      "dynamodb:UpdateItem",
    ]
    resources = [var.table_arn]
  }
}

data "aws_iam_policy_document" "mark_failed" {
  source_policy_documents = [data.aws_iam_policy_document.logs["mark_failed"].json]

  statement {
    sid       = "FailBatch"
    actions   = ["dynamodb:GetItem", "dynamodb:BatchWriteItem"]
    resources = [var.table_arn]
  }
}

data "aws_iam_policy_document" "api" {
  source_policy_documents = [data.aws_iam_policy_document.logs["api"].json]

  statement {
    sid       = "ReadBatches"
    actions   = ["dynamodb:GetItem", "dynamodb:Query"]
    resources = [var.table_arn]
  }

  statement {
    sid       = "ReadReports"
    actions   = ["s3:GetObject"]
    resources = ["${local.objects}reports/*"]
  }

  statement {
    sid       = "TellMissingFromForbidden"
    actions   = ["s3:ListBucket"]
    resources = [var.bucket_arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["reports/*"]
    }
  }
}

locals {
  policies = {
    normalize      = data.aws_iam_policy_document.normalize.json
    classify_chunk = data.aws_iam_policy_document.classify_chunk.json
    dedupe         = data.aws_iam_policy_document.dedupe.json
    summarize      = data.aws_iam_policy_document.summarize.json
    finalize       = data.aws_iam_policy_document.finalize.json
    mark_failed    = data.aws_iam_policy_document.mark_failed.json
    api            = data.aws_iam_policy_document.api.json
  }
}

resource "aws_iam_role_policy" "function" {
  for_each = local.functions

  name   = "${var.name_prefix}-${each.key}"
  role   = aws_iam_role.function[each.key].id
  policy = local.policies[each.key]
}
