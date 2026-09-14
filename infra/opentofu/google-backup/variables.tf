variable "project_id" {
  description = "Existing Google Cloud project that owns dojo's Google APIs."
  type        = string
}

variable "additional_allowed_referrers" {
  description = "Deployment-specific browser origins allowed to use the Picker API key."
  type        = list(string)
  default     = []
}
