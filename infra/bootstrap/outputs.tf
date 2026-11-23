output "state_bucket_name" {
  description = "Bucket to reference from the S3 backend of every other stack."
  value       = aws_s3_bucket.state.id
}

output "state_bucket_arn" {
  description = "ARN of the state bucket, for scoping IAM policies."
  value       = aws_s3_bucket.state.arn
}

output "ci_plan_role_arn" {
  description = "Set as the AWS_PLAN_ROLE_ARN repository variable in GitHub."
  value       = aws_iam_role.ci_plan.arn
}

output "ci_eval_role_arn" {
  description = "Set as the AWS_EVAL_ROLE_ARN repository variable in GitHub."
  value       = aws_iam_role.ci_eval.arn
}
