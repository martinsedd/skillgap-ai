data "aws_ami" "ubuntu" {
  most_recent = true
  owners = ["099720109477"] # Canonical

  filter {
    name = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name = "virtualization-type"
    values = ["hvm"]
  }
}

# Create VPC (using default for free tier simplicity)
data "aws_vpc" "default" {
  default = true
}

# Get default subnets
data "aws_subnets" "default" {
  filter {
    name = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# EC2 Instance
resource "aws_instance" "app" {
  ami = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name = var.key_name

  availability_zone = "us-east-1a"

  vpc_security_group_ids = var.security_group_ids
  iam_instance_profile = var.iam_instance_role

  subnet_id = tolist(data.aws_subnets.default.ids)[0]

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted = true
  }

  user_data = templatefile("${path.module}/user_data.sh", {
    s3_bucket_name = var.s3_bucket_name
    project_name = var.project_name
    environment = var.environment
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-ec2"
  }

  user_data_replace_on_change = true
}

resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-${var.environment}-eip"
  }
}
