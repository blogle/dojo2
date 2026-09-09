output "backup_service_account_email" {
  description = "Share the user-created Google Drive folder with this address."
  value       = google_service_account.backup.email
}

output "backup_service_account_name" {
  value = google_service_account.backup.name
}
