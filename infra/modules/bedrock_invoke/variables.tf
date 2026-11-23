variable "profile_ids" {
  description = "Global cross-Region inference profile IDs of the Claude models the role may invoke."
  type        = set(string)

  validation {
    condition     = length(var.profile_ids) > 0 && alltrue([for profile in var.profile_ids : startswith(profile, "global.")])
    error_message = "Claude stages must use a global inference profile; other model IDs need their own IAM statements."
  }
}
