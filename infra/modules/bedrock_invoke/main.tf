data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

locals {
  region    = data.aws_region.current.region
  account   = data.aws_caller_identity.current.account_id
  partition = data.aws_partition.current.partition

  profile_arns = [
    for profile in sort(tolist(var.profile_ids)) :
    "arn:${local.partition}:bedrock:${local.region}:${local.account}:inference-profile/${profile}"
  ]
  model_names = [for profile in sort(tolist(var.profile_ids)) : trimprefix(profile, "global.")]
}

data "aws_iam_policy_document" "invoke" {
  statement {
    sid       = "GrantGlobalCrisInferenceProfileRegionAccess"
    actions   = ["bedrock:InvokeModel"]
    resources = local.profile_arns

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [local.region]
    }
  }

  statement {
    sid       = "GrantGlobalCrisInferenceProfileInRegionModelAccess"
    actions   = ["bedrock:InvokeModel"]
    resources = [for model in local.model_names : "arn:${local.partition}:bedrock:${local.region}::foundation-model/${model}"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [local.region]
    }

    condition {
      test     = "StringEquals"
      variable = "bedrock:InferenceProfileArn"
      values   = local.profile_arns
    }
  }

  statement {
    sid       = "GrantGlobalCrisInferenceProfileGlobalModelAccess"
    actions   = ["bedrock:InvokeModel"]
    resources = [for model in local.model_names : "arn:${local.partition}:bedrock:::foundation-model/${model}"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = ["unspecified"]
    }

    condition {
      test     = "StringEquals"
      variable = "bedrock:InferenceProfileArn"
      values   = local.profile_arns
    }
  }
}
