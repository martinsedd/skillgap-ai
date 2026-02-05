variable "aws_region" {
  description = "AWS region for resources"
  type = string
  default = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type = string
  default = "skillgap"
}

variable "environment" {
  description = "Environment (prod, staging, dev)"
  type = string
  default = "prod"
}

variable "instance_type" {
  description = "EC2 instance type"
  type = string
  default = "t2.micro"
}

variable "ssh_key_name" {
  description = "Name of SSH key pair for EC2 access"
  type = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH"
  type = string
}
