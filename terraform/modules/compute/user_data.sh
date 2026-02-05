#!/bin/bash
set -e

# Log everything
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "Starting SkillGap EC2 setup..."

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |
  tee /etc/apt/sources.list.d/docker.list >/dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Install AWS CLI v2
cd /tmp
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
apt-get install -y unzip
unzip awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Create app directory
mkdir -p /opt/${project_name}
chown ubuntu:ubuntu /opt/${project_name}

# Install Docker Compose standalone (for convenience)
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Setup systemd service for SkillGap
cat >/etc/systemd/system/${project_name}.service <<EOF
[Unit]
Description=SkillGap Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/${project_name}
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

echo "SkillGap EC2 setup complete!"
echo "Instance is ready for deployment."
