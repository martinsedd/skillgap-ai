terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Store state in S3 (uncomment after first apply)
  # backend "s3" {
  #   bucket = "skillgap-terraform-state"
  #   key = "prod/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project = "SkillGap"
      Environment = var.environment
      ManagedBy = "Terraform"
    }
  }
}

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}

# Security module (IAM roles, security groups)
module "security" {
  source = "./modules/security"

  project_name = var.project_name
  environment = var.environment
  vpc_id = module.compute.vpc_id
  allowed_ssh_cidr = var.allowed_ssh_cidr
}

# Storage module (S3 bucket for resumes)
module "storage" {
  source = "./modules/storage"

  project_name = var.project_name
  environment = var.environment
  account_id = data.aws_caller_identity.current.account_id
}

# Compute module (EC2 instance)
module "compute" {
  source = "./modules/compute"

  project_name = var.project_name
  environment = var.environment
  instance_type = var.instance_type
  key_name = var.ssh_key_name
  iam_instance_role = module.security.ec2_instance_profile_name
  security_group_ids = [module.security.ec2_security_group_id]

  # Pass bucket name to user data for Docker env
  s3_bucket_name = module.storage.bucket_name
}
