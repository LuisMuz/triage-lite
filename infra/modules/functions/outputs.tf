output "function_arns" {
  description = "Function ARNs by stage, for the state machine."
  value       = { for name, function in aws_lambda_function.function : name => function.arn }
}

output "invoke_arns" {
  description = "Invoke ARNs by function, for API Gateway integrations."
  value       = { for name, function in aws_lambda_function.function : name => function.invoke_arn }
}

output "function_names" {
  description = "Function names by stage, for aws lambda invoke."
  value       = { for name, function in aws_lambda_function.function : name => function.function_name }
}

output "bedrock_models" {
  description = "Model IDs read from config/models.toml that the IAM policies allow."
  value       = merge(local.stage_models, { embedding = local.embedding_model })
}
