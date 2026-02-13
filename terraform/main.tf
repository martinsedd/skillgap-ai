
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "skillgap-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SkillGap"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_subnet" "app_az" {
  availability_zone = "us-east-1a"
  default_for_az    = true
  vpc_id            = data.aws_vpc.default.id
}

module "security" {
  source = "./modules/security"

  project_name     = var.project_name
  environment      = var.environment
  vpc_id           = data.aws_vpc.default.id
  allowed_ssh_cidr = var.allowed_ssh_cidr
}

module "storage" {
  source = "./modules/storage"

  project_name = var.project_name
  environment  = var.environment
  account_id   = data.aws_caller_identity.current.account_id
}

module "compute" {
  source = "./modules/compute"

  project_name       = var.project_name
  environment        = var.environment
  instance_type      = var.instance_type
  key_name           = var.ssh_key_name
  iam_instance_role  = module.security.ec2_instance_profile_name
  security_group_ids = [module.security.ec2_security_group_id]
  s3_bucket_name     = module.storage.bucket_name
  subnet_id          = data.aws_subnet.app_az.id
  aws_account_id     = data.aws_caller_identity.current.account_id
}

module "database" {
  source = "./modules/database"

  project_name         = var.project_name
  environment          = var.environment
  subnet_ids           = data.aws_subnets.default.ids
  db_security_group_id = module.security.rds_security_group_id
  monitoring_role_arn  = module.security.rds_monitoring_role_arn

  db_instance_class       = var.db_instance_class
  db_allocated_storage    = var.db_allocated_storage
  backup_retention_period = 0
  multi_az                = false
  deletion_protection     = true
  skip_final_snapshot     = false
}
