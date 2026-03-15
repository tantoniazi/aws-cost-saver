# aws-cost-saver Terraform root
# Deploy Lambda + EventBridge + IAM for scheduled cost saving

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment_names" {
  description = "Environments to run cost-saver for (e.g. dev, staging, training)"
  type        = list(string)
  default     = ["dev", "staging", "training"]
}

variable "config_s3_bucket" {
  description = "Optional S3 bucket containing config/environments.yaml (key: config/environments.yaml)"
  type        = string
  default     = ""
}

variable "config_s3_key" {
  description = "S3 key for config file if config_s3_bucket is set"
  type        = string
  default     = "config/environments.yaml"
}
