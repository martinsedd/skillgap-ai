output "ec2_security_group_id" {
  description = "Security group ID for EC2"
  value = aws_security_group.ec2.id
}

output "ec2_iam_role_arn" {
  description = "IAM role ARN for EC2"
  value = aws_iam_role.ec2.arn
}

output "ec2_instance_profile_name" {
  description = "IAM instance profile name"
  value = aws_iam_instance_profile.ec2.name
}
