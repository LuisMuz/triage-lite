output "dashboard_url" {
  description = "Console link to the pipeline dashboard."
  value       = "https://${local.region}.console.aws.amazon.com/cloudwatch/home?region=${local.region}#dashboards/dashboard/${aws_cloudwatch_dashboard.pipeline.dashboard_name}"
}

output "alarm_names" {
  description = "The three alarms that publish to the alerts topic."
  value = [
    aws_cloudwatch_metric_alarm.run_failed.alarm_name,
    aws_cloudwatch_metric_alarm.function_errors.alarm_name,
    aws_cloudwatch_metric_alarm.daily_cost.alarm_name,
  ]
}

output "saved_queries" {
  description = "Logs Insights saved query names, shown as a folder in the console."
  value       = [for query in aws_cloudwatch_query_definition.saved : query.name]
}
