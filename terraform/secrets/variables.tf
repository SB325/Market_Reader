variable "app_secrets_json" {
  description = "A JSON string containing all application secrets"
  type        = string
  sensitive   = true
}

variable "aws_region" {
  description = "Target AWS region"
  type        = string
  default     = "us-east-1"
}