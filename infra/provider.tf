provider "aws" {
  region = var.aws_region
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "nextime-frame-state-bucket"
    key            = "lambda-sender/terraform.tfstate"
    region         = "eu-central-1"
    encrypt        = true
  }
}
