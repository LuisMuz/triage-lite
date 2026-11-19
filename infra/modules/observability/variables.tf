variable "name_prefix" {
  description = "Prefix for the dashboard, alarm and saved query names."
  type        = string
}

variable "metrics_namespace" {
  description = "CloudWatch namespace of the EMF metrics the functions write."
  type        = string
}

variable "function_names" {
  description = "Function names by function, from the functions module; every one is watched for errors."
  type        = map(string)
}

variable "log_group_names" {
  description = "Log group names by function, from the functions module."
  type        = map(string)

  validation {
    condition = alltrue([
      for function in ["classify_chunk", "dedupe", "summarize"] :
      contains(keys(var.log_group_names), function)
    ])
    error_message = "log_group_names needs classify_chunk, dedupe and summarize, the functions that call models."
  }
}

variable "state_machine_arn" {
  description = "Pipeline state machine whose failed or timed-out runs raise an alarm."
  type        = string
}

variable "alerts_topic_arn" {
  description = "SNS topic the alarms publish to; the pipeline's own failure message goes there too."
  type        = string
}

variable "alert_email" {
  description = "Address subscribed to the alerts topic; null leaves the topic without a subscriber."
  type        = string
  default     = null
  sensitive   = true

  validation {
    condition     = var.alert_email == null || can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.alert_email))
    error_message = "alert_email must be an email address or null."
  }
}

variable "daily_cost_alarm_usd" {
  description = "Model spend over a rolling 24 hours that raises an alarm (TL-08 alert level)."
  type        = number
  default     = 0.5
}

variable "lambda_errors_alarm" {
  description = "Function errors across all functions within 5 minutes that raise an alarm."
  type        = number
  default     = 3
}
