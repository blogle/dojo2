provider "google" {
  project = var.project_id
}

data "google_project" "current" {
  project_id = var.project_id
}

locals {
  google_services = toset([
    "drive.googleapis.com",
    "sheets.googleapis.com",
    "picker.googleapis.com",
    "apikeys.googleapis.com",
  ])
}

resource "google_project_service" "required" {
  project            = var.project_id
  for_each           = local.google_services
  service            = each.value
  disable_on_destroy = false
}

resource "google_apikeys_key" "picker" {
  name         = "dojo-picker"
  display_name = "dojo Google Picker"

  restrictions {
    browser_key_restrictions {
      allowed_referrers = concat(
        [
          "http://localhost:5173/*",
          "https://docs.google.com/*",
        ],
        var.additional_allowed_referrers,
      )
    }

    api_targets {
      service = "picker.googleapis.com"
    }

    api_targets {
      service = "drive.googleapis.com"
    }
  }

  depends_on = [google_project_service.required]
}
