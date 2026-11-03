variable "region" {
  description = "AWS region for the bootstrap resources."
  type        = string
  default     = "us-east-1"
}

variable "env" {
  description = "Value of the env cost allocation tag."
  type        = string
  default     = "demo"
}

variable "owner" {
  description = "Value of the owner cost allocation tag."
  type        = string
  default     = "luis"
}

variable "state_bucket_name" {
  description = "Globally unique name of the S3 bucket that stores Terraform state."
  type        = string
  default     = "triage-state-tf"
}

variable "noncurrent_state_retention_days" {
  description = "Days to keep old versions of state files before they expire."
  type        = number
  default     = 90
}

variable "incomplete_upload_retention_days" {
  description = "Days before an unfinished multipart upload is aborted."
  type        = number
  default     = 7
}

variable "budget_name" {
  description = "Name of the account-wide monthly cost budget."
  type        = string
  default     = "TriageLiteTotal"
}

variable "budget_limit_usd" {
  description = "Monthly limit of the cost budget, in USD."
  type        = string
  default     = "30.0"
}

variable "budget_alert_email" {
  description = "Address that receives budget alerts. Set it in the gitignored terraform.tfvars."
  type        = string
}
