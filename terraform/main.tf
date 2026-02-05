terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ca-central-1"
}

module "storage" {
  source = "./modules/storage"
}

output "bucket_name" {
  value = module.storage.bucket_name
}
