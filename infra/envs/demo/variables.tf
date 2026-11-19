variable "region" {
  description = "AWS region for the demo environment."
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

variable "alert_email" {
  description = "Address that receives alarm and failed-batch emails; set it in the gitignored terraform.tfvars."
  type        = string
  default     = null
  sensitive   = true
}
