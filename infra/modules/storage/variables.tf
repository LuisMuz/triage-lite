variable "bucket_name" {
  description = "Globally unique name of the data bucket."
  type        = string
}

variable "table_name" {
  description = "Name of the DynamoDB table."
  type        = string
}

variable "force_destroy" {
  description = "Whether terraform destroy may delete the bucket while it still holds objects."
  type        = bool
  default     = false
}

variable "work_retention_days" {
  description = "Days before objects under work/ expire."
  type        = number
  default     = 7
}

variable "incomplete_upload_retention_days" {
  description = "Days before an unfinished multipart upload is aborted."
  type        = number
  default     = 7
}
