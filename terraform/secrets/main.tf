provider "aws" {
  region = "us-east-1" 
}

resource "aws_secretsmanager_secret" "app_secrets" {
  name = "prod/app/config"
}

resource "aws_secretsmanager_secret_version" "app_secrets_val" {
  secret_id     = aws_secretsmanager_secret.app_secrets.id
  secret_string = var.app_secrets_json
}