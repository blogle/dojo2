variable "project_id" {
  description = "Existing Google Cloud project that owns the dojo backup identity."
  type        = string
}

variable "service_account_id" {
  description = "Account ID for the deployment-specific backup identity."
  type        = string
  default     = "dojo-backup"
}
