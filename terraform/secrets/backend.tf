terraform {
  backend "s3" {
    bucket         = "tf-state-market-reader" # Your unique bucket name
    key            = "prod/secrets-manager/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true                         # Forces Server-Side Encryption (AES-256)
    dynamodb_table = "terraform-lock-table"       # Prevents concurrent runs
  }
}