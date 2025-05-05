provider "aws" {
  region = "ap-south-1"
}

resource "aws_instance" "SAGE" {
  ami           = "ami-0e35ddab05955cf57"
  instance_type = "t2.medium"

  tags = {
    Name = "SAGE-EC2"
  }

  key_name = "devops"  # Make sure the key pair exists in AWS

  security_groups = [aws_security_group.sg.name]

  associate_public_ip_address = true
}

resource "aws_security_group" "sg" {
  name        = "allow-ssh"
  description = "Allow SSH access to EC2 instances"

  ingress {
    from_port   = 22   # SSH access
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80   # HTTP access
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000  # Grafana access
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9090  # Prometheus access
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
