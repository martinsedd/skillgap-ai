output "ec2_public_ip" {
  description = "Public IP of EC2 instance"
  value = module.compute.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value = module.compute.instance_id
}

output "s3_bucket_name" {
  description = "S3 bucket name for resumes"
  value = module.storage.bucket_name
}

output "ec2_connect_command" {
  description = "SSH command to connect to EC2"
  value = "ssh -i ~/.ssh/${var.ssh_key_name}.pem ubuntu@${module.compute.public_ip}"
}
