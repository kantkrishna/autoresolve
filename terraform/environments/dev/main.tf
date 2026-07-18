terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# 1. RDS PostgreSQL Database (State & Memory)
resource "aws_db_instance" "autoresolve_db" {
  identifier           = "autoresolve-state"
  engine               = "postgres"
  engine_version       = "15.3"
  instance_class       = "db.t4g.micro"
  allocated_storage    = 20
  db_name              = "autoresolve"
  username             = "ar_admin"
  password             = var.db_password # Injected securely via pipeline
  skip_final_snapshot  = true
  publicly_accessible  = false
}

# 2. Managed Kafka (MSK) for Event Bus
resource "aws_msk_cluster" "autoresolve_events" {
  cluster_name           = "autoresolve-event-bus"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = 2

  broker_node_group_info {
    instance_type   = "kafka.t3.small"
    client_subnets  = var.private_subnets
    security_groups = [aws_security_group.kafka_sg.id]
  }
}

# (EKS Cluster definition assumed available via internal enterprise module)