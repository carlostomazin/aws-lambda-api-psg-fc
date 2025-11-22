terraform {
  required_version = ">= 6.22.1"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  backend "s3" {
    bucket         = "tf-state-bucket-529160768027"
    key            = "infra/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf-state-lock-table-529160768027"
  }
}

provider "aws" {
  region = "us-east-1"
}