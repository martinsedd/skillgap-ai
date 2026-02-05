variable "project_name" {
  description = "Project name"
  type = string
}

variable "environment" {
  description = "Environment"
  type = string
}

variable "vpc_id" {
  description = "VPC ID"
  type = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowd to SSH"
  type = string
  default = "0.0.0.0/0" # Will be overriden by root variable
}
