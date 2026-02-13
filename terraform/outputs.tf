output "ec2_public_ip" {
  description = "Public IP of EC2 instance"
  value       = module.compute.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = module.compute.instance_id
}

output "s3_bucket_name" {
  description = "S3 bucket name for resumes"
  value       = module.storage.bucket_name
}

output "ec2_connect_command" {
  description = "SSH command to connect to EC2"
  value       = "ssh -i ~/.ssh/${var.ssh_key_name}.pem ubuntu@${module.compute.public_ip}"
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.database.db_endpoint
}

output "rds_host" {
  description = "RDS PostgreSQL hostname"
  value       = module.database.db_host
}

output "db_password_ssm_path" {
  description = "SSM path to retrieve the DB password"
  value       = module.database.db_password_ssm_path
}

output "database_url_template" {
  description = "DATABASE_URL template (password must be retrieved from SSM)"
  value       = "postgresql://${module.database.db_username}:<password>@${module.database.db_host}:${module.database.db_port}/${module.database.db_name}"
  sensitive   = false
}
