output "bucket_name" {
  description = "Name of the data bucket."
  value       = aws_s3_bucket.data.id
}

output "bucket_arn" {
  description = "ARN of the data bucket, for scoping IAM policies."
  value       = aws_s3_bucket.data.arn
}

output "table_name" {
  description = "Name of the DynamoDB table."
  value       = aws_dynamodb_table.main.name
}

output "table_arn" {
  description = "ARN of the DynamoDB table, for scoping IAM policies."
  value       = aws_dynamodb_table.main.arn
}
