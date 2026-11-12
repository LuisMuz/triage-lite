variable "name_prefix" {
  description = "Prefix for function, role and log group names."
  type        = string
}

variable "package_dir" {
  description = "Folder holding code.zip and layer.zip from make build."
  type        = string
}

variable "models_config" {
  description = "Contents of config/models.toml; Bedrock permissions follow the models it names."
  type        = string
}

variable "bucket_name" {
  description = "Name of the data bucket."
  type        = string
}

variable "bucket_arn" {
  description = "ARN of the data bucket."
  type        = string
}

variable "table_name" {
  description = "Name of the DynamoDB table."
  type        = string
}

variable "table_arn" {
  description = "ARN of the DynamoDB table."
  type        = string
}

variable "log_level" {
  description = "Application log level."
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR"], var.log_level)
    error_message = "log_level must be DEBUG, INFO, WARNING or ERROR."
  }
}

variable "log_retention_days" {
  description = "Days CloudWatch keeps function logs."
  type        = number
  default     = 14
}
