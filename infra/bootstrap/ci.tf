data "aws_partition" "current" {}

locals {
  github_oidc_host = "token.actions.githubusercontent.com"
  models_config    = file("${path.root}/../../config/models.toml")
  claude_profiles = toset([
    for stage in ["classify", "dedupe_judge", "summarize"] :
    one(regexall("(?m)^model_id = \"([^\"]+)\"", one(regexall("(?ms)^\\[stages\\.${stage}\\]$(.*?)(?:^\\[|\\z)", local.models_config))[0]))[0]
  ])
}

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://${local.github_oidc_host}"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_policy_document" "trust_plan" {
  statement {
    sid     = "GitHubPullRequestsOfThisRepo"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.github_oidc_host}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.github_oidc_host}:sub"
      values   = ["repo:${var.github_repository}:pull_request"]
    }
  }
}

data "aws_iam_policy_document" "trust_eval" {
  statement {
    sid     = "GitHubPullRequestsAndMainOfThisRepo"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.github_oidc_host}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.github_oidc_host}:sub"
      values = [
        "repo:${var.github_repository}:pull_request",
        "repo:${var.github_repository}:ref:refs/heads/main",
      ]
    }
  }
}

resource "aws_iam_role" "ci_plan" {
  name                 = "triagelite-plan"
  description          = "terraform plan from GitHub Actions pull requests; read-only, plans run with -lock=false."
  assume_role_policy   = data.aws_iam_policy_document.trust_plan.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy_attachment" "ci_plan_read_only" {
  role       = aws_iam_role.ci_plan.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/ReadOnlyAccess"
}

data "aws_iam_policy_document" "ci_plan_no_data" {
  statement {
    sid           = "NoObjectsOutsideTheStateBucket"
    effect        = "Deny"
    actions       = ["s3:GetObject", "s3:GetObjectVersion", "s3:GetObjectAttributes"]
    not_resources = ["${aws_s3_bucket.state.arn}/*"]
  }

  statement {
    sid    = "NoTableItems"
    effect = "Deny"
    actions = [
      "dynamodb:BatchGetItem",
      "dynamodb:GetItem",
      "dynamodb:GetRecords",
      "dynamodb:PartiQLSelect",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "NoLogContents"
    effect = "Deny"
    actions = [
      "logs:FilterLogEvents",
      "logs:GetLogEvents",
      "logs:GetLogRecord",
      "logs:GetQueryResults",
      "logs:StartLiveTail",
      "logs:StartQuery",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "NoExecutionPayloads"
    effect    = "Deny"
    actions   = ["states:DescribeExecution", "states:GetExecutionHistory"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ci_plan_no_data" {
  name   = "no-data-reads"
  role   = aws_iam_role.ci_plan.id
  policy = data.aws_iam_policy_document.ci_plan_no_data.json
}

module "ci_eval_bedrock" {
  source = "../modules/bedrock_invoke"

  profile_ids = local.claude_profiles
}

resource "aws_iam_role" "ci_eval" {
  name                 = "triagelite-eval"
  description          = "Eval gate from GitHub Actions: Bedrock InvokeModel on the configured Claude profiles only."
  assume_role_policy   = data.aws_iam_policy_document.trust_eval.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy" "ci_eval_bedrock" {
  name   = "invoke-configured-claude"
  role   = aws_iam_role.ci_eval.id
  policy = module.ci_eval_bedrock.policy_json
}
