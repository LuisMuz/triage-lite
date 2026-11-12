variable "name_prefix" {
  description = "Prefix for the API and log group names."
  type        = string
}

variable "function_name" {
  description = "Name of the api function, for the invoke permission."
  type        = string
}

variable "function_invoke_arn" {
  description = "Invoke ARN of the api function."
  type        = string
}

variable "throttling_rate_limit" {
  description = "Steady requests per second across the stage; cheap protection against abuse."
  type        = number
  default     = 10
}

variable "throttling_burst_limit" {
  description = "Requests the stage absorbs at once before throttling."
  type        = number
  default     = 20
}

variable "integration_timeout_ms" {
  description = "How long API Gateway waits for the function; just above its 10 s timeout."
  type        = number
  default     = 11000

  validation {
    condition     = var.integration_timeout_ms >= 50 && var.integration_timeout_ms <= 30000
    error_message = "integration_timeout_ms must be between 50 and 30000."
  }
}

variable "log_retention_days" {
  description = "Days to keep access logs."
  type        = number
  default     = 14
}
