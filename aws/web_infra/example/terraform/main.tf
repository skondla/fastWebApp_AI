provider "aws" {
  region = "us-west-2"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "main-vpc" }
}

# Public Subnet1
resource "aws_subnet" "public1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone = "us-west-2a"
  tags = { Name = "public-subnet1" }
}

#Public Subnet2
resource "aws_subnet" "public2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  map_public_ip_on_launch = true
  availability_zone = "us-west-2b"
  tags = { Name = "public-subnet2" }
}

#Public Subnet2
resource "aws_subnet" "public3" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.5.0/24"
  map_public_ip_on_launch = true
  availability_zone = "us-west-2c"
  tags = { Name = "public-subnet3" }
}


# Private Subnet1
resource "aws_subnet" "private1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-west-2a"
  tags = { Name = "private-subnet1" }
}

# Private Subnet1
resource "aws_subnet" "private2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.4.0/24"
  availability_zone = "us-west-2b"
  tags = { Name = "private-subnet2" }
}
# Private Subnet3
resource "aws_subnet" "private3" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.6.0/24"
  availability_zone = "us-west-2c"
  tags = { Name = "private-subnet3" }
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags = { Name = "main-igw" }
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat_eip" {
  # vpc argument is deprecated and removed
  # No replacement needed as it's not required for this configuration
  tags = { Name = "nat-eip" }
}

# NAT Gateway1
resource "aws_nat_gateway" "nat1" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public1.id
  tags = { Name = "nat-gateway1" }
}


# # NAT Gateway2
# resource "aws_nat_gateway" "nat2" {
#   allocation_id = aws_eip.nat_eip.id
#   subnet_id     = [aws_subnet.public2.id]
#   tags = { Name = "nat-gateway2" }
# }

# # NAT Gateway1
# resource "aws_nat_gateway" "nat2" {
#   allocation_id = aws_eip.nat_eip.id
#   subnet_id     = [aws_subnet.public3.id]
#   tags = { Name = "nat-gateway3" }
# }

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  tags = { Name = "public-rt" }

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "public1" {
  subnet_id      = aws_subnet.public1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public2" {
  subnet_id      = aws_subnet.public2.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public3" {
  subnet_id      = aws_subnet.public3.id
  route_table_id = aws_route_table.public.id
}


# Private Route Table with NAT Gateway
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  tags = { Name = "private-rt" }

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat1.id
  }
}

resource "aws_route_table_association" "private1" {
  subnet_id      = aws_subnet.private1.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private2" {
  subnet_id      = aws_subnet.private2.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private3" {
  subnet_id      = aws_subnet.private3.id
  route_table_id = aws_route_table.private.id
}


# Security Group for ALB
resource "aws_security_group" "alb_sg" {
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

   ingress {
    from_port   = 443
    to_port     = 443
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


# Security Group for EC2 Instances
resource "aws_security_group" "allow_ssh" {
  vpc_id = aws_vpc.main.id
  name   = "allow-ssh"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0", "10.20.30.200/32"]
  }

  ingress {
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0", "20.30.200/32"]
}

ingress {
  from_port   = 443
  to_port     = 443
  protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0", "20.30.200/32"]
}

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "allow-ssh" }
}

# Security Group for EC2 Instances to allow traffic from ALB
resource "aws_security_group" "instance_sg" {
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ALB
resource "aws_lb" "app" {
  name               = "app-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public1.id, aws_subnet.public2.id, aws_subnet.public3.id]
    tags = { Name = "app-lb" }
}

resource "aws_lb_target_group" "app_tg" {
  name     = "app-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/"
    protocol            = "HTTP"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }

  tags = {
    Name = "app-tg"
  }
}

# Attach EC2 instances to the target group
resource "aws_lb_target_group_attachment" "web1_80" {
  target_group_arn = aws_lb_target_group.app_tg.arn
  target_id        = aws_instance.app[0].id
  port             = 80
}

resource "aws_lb_target_group_attachment" "web2_80" {
  target_group_arn = aws_lb_target_group.app_tg.arn
  target_id        = aws_instance.app[1].id
  port             = 80
}

resource "aws_lb_target_group_attachment" "web3_80" {
  target_group_arn = aws_lb_target_group.app_tg.arn
  target_id        = aws_instance.app[2].id
  port             = 80
}

resource "aws_lb_listener" "app_listener_80" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
}

#Import SSL Certificate

resource "aws_acm_certificate" "imported_cert" {
  private_key       = file("certs/key.pem")
  certificate_body  = file("certs/certificate.pem")
  certificate_chain = file("certs/certificate_chain.pem")

  tags = {
    Name = "my-imported-cert"
  }
}

resource "aws_lb_listener" "app_listener_443" {
  load_balancer_arn = aws_lb.app.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"  # You can pick another if needed

  certificate_arn = aws_acm_certificate.imported_cert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
}

# Attach EC2 instances to the target group
resource "aws_lb_target_group_attachment" "web1_443" {
  target_group_arn = aws_lb_target_group.app_tg.arn
  target_id        = aws_instance.app[0].id
  port             = 443
}

resource "aws_lb_target_group_attachment" "web2_443" {
  target_group_arn = aws_lb_target_group.app_tg.arn
  target_id        = aws_instance.app[1].id
  port             = 443
}

resource "aws_lb_target_group_attachment" "web3_443" {
  target_group_arn = aws_lb_target_group.app_tg.arn
  target_id        = aws_instance.app[2].id
  port             = 443
}



# EC2 Instances
resource "aws_instance" "app" {
  count                       = 3
  ami                         = "ami-087f352c165340ea1" # Amazon Linux 2 for us-west-2
  instance_type               = "t2.micro"
  subnet_id                   = [aws_subnet.private1.id, aws_subnet.private2.id, aws_subnet.private3.id][count.index % 3]
  vpc_security_group_ids      = [aws_security_group.instance_sg.id, aws_security_group.allow_ssh.id]
  associate_public_ip_address = false
  key_name                    = "ssh-key2-us-west-2" # Replace with your actual key name
  user_data                   = file("../ec2/bootstrap.sh")

  tags = {
    Name = "app-instance-${count.index}"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# EC2 Instance in Public Subnet using NAT Gateway

resource "aws_instance" "public_ec2" {
  ami                         = "ami-087f352c165340ea1" # Amazon Linux 2 AMI in us-west-2
  instance_type               = "t2.micro"
  subnet_id                   = [aws_subnet.public1.id, aws_subnet.public2.id, aws_subnet.public3.id][0]
  vpc_security_group_ids      = [aws_security_group.allow_ssh.id]
  associate_public_ip_address = true
  key_name                    = "ssh-key2-us-west-2" # Replace with your actual SSH key name
  user_data                   = file("../bash/bootstrap2.sh")

  tags = {
    Name = "public-ec2"
  }
}

# EC2 Instance in Private Subnet using NAT Gateway

# resource "aws_instance" "private_ec2" {
#   ami                         = "ami-087f352c165340ea1" # Amazon Linux 2 AMI in us-west-2
#   instance_type               = "t2.micro"
#   subnet_id                   = aws_subnet.private.id
#   vpc_security_group_ids      = [aws_security_group.allow_ssh.id]
#   associate_public_ip_address = false
#   key_name                    = "ssh-key2-us-west-2" # Replace with your actual SSH key name
#   user_data                   = file("../bash/bootstrap2.sh")

#   tags = {
#     Name = "private-ec2"
#   }
# }


# resource "aws_instance" "private_ec2" {
#   ami                         = "ami-087f352c165340ea1" # Amazon Linux 2 AMI in us-west-2
#   instance_type               = "t2.micro"
#   subnet_id                   = aws_subnet.private.id
#   vpc_security_group_ids      = [aws_security_group.allow_ssh.id]
#   associate_public_ip_address = false
#     user_data = file("../bash/bootstrap2.sh")
#     #user_data = file("${path.module}/setup.sh")
# #   user_data = <<-EOF
# #               #!/bin/bash
# #               yum update -y
# #               yum install -y curl
# #               curl https://example.com
# #               EOF

#   tags = { Name = "private-ec2" }
# }
