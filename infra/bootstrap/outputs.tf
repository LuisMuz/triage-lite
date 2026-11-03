output "state_bucket_name" {
  description = "Bucket to reference from the S3 backend of every other stack."
  value       = aws_s3_bucket.state.id
}

output "state_bucket_arn" {
  description = "ARN of the state bucket, for scoping IAM policies."
  value       = aws_s3_bucket.state.arn
}
