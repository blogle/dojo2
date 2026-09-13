output "picker_api_key" {
  description = "Restricted browser API key used by Google Picker."
  value       = google_apikeys_key.picker.key_string
  sensitive   = true
}

output "picker_app_id" {
  description = "Google Cloud project number used as the Google Picker App ID."
  value       = data.google_project.current.number
}
