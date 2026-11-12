variable "name_prefix" {
  description = "Prefix for the state machine, rule, topic and role names."
  type        = string
}

variable "function_arns" {
  description = "Function ARNs by stage, from the functions module."
  type        = map(string)

  validation {
    condition = alltrue([
      for stage in ["normalize", "classify_chunk", "dedupe", "summarize", "finalize", "mark_failed"] :
      contains(keys(var.function_arns), stage)
    ])
    error_message = "function_arns needs normalize, classify_chunk, dedupe, summarize, finalize and mark_failed."
  }
}

variable "bucket_name" {
  description = "Data bucket whose uploads start the pipeline; it must send events to EventBridge."
  type        = string
}

variable "upload_prefix" {
  description = "Key prefix of the CSV uploads that start a run."
  type        = string
  default     = "incoming/"
}

variable "max_chunk_concurrency" {
  description = "Chunks classified at the same time; keeps Bedrock requests under the account quota."
  type        = number
  default     = 3

  validation {
    condition     = var.max_chunk_concurrency >= 1 && var.max_chunk_concurrency <= 10
    error_message = "max_chunk_concurrency must be between 1 and 10."
  }
}

variable "execution_timeout_seconds" {
  description = "Hard stop for one run, so a stuck batch cannot keep retrying paid calls."
  type        = number
  default     = 3600
}
