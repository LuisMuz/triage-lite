output "state_machine_arn" {
  description = "ARN of the pipeline state machine."
  value       = aws_sfn_state_machine.pipeline.arn
}

output "state_machine_name" {
  description = "Name of the pipeline state machine."
  value       = aws_sfn_state_machine.pipeline.name
}

output "alerts_topic_arn" {
  description = "SNS topic that receives failed batches; subscriptions come with the observability module."
  value       = aws_sns_topic.alerts.arn
}
