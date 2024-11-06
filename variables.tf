variable "redcap_secret" {
  description = "The secret value for REDCap"
  type        = string
  sensitive   = true
}

variable "true_colours_secret" {
  description = "The secret value for True Colours"
  type        = string
  sensitive   = true
}

variable "mailgun_secret" {
  description = "The secret value for Mailgun"
  type        = string
  sensitive   = true
}
