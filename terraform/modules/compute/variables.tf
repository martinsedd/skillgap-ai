variable "project_name" {
  description = "Project name"
  type = string
}

variable "environment" {
  description = "Environment"
  type = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type = string
}

variable "key_name" {
  description = "SSH key pair name"
  type = string
}

variable "iam_instance_role" {
  description = "IAM instance profile name"
  type = string
}

variable "security_group_ids" {
  description = "List of security group IDs"
  type = list(string)
}

variable "s3_bucket_name" {
  description = "S3 bucket name for resumes"
  type = string
}
