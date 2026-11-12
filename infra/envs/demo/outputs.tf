output "data_bucket_name" {
  description = "Bucket that receives CSV uploads and holds run output."
  value       = module.storage.bucket_name
}

output "table_name" {
  description = "DynamoDB table with batches, incidents and clusters."
  value       = module.storage.table_name
}

output "function_names" {
  description = "Lambda function names by stage."
  value       = module.functions.function_names
}

output "bedrock_models" {
  description = "Model IDs the Lambda roles may invoke."
  value       = module.functions.bedrock_models
}

output "state_machine_arn" {
  description = "Pipeline state machine; uploads to incoming/ start it."
  value       = module.pipeline.state_machine_arn
}

output "alerts_topic_arn" {
  description = "SNS topic for failed batches."
  value       = module.pipeline.alerts_topic_arn
}
