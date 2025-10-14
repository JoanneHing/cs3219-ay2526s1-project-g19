# =============================================================================
# PeerPrep AWS ECS Infrastructure - Main Configuration
# =============================================================================
# Phase 1: VPC and Networking Foundation
# This file orchestrates all infrastructure modules
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Optional: Uncomment to use S3 backend for state management
  # backend "s3" {
  #   bucket         = "peerprep-terraform-state"
  #   key            = "ecs/terraform.tfstate"
  #   region         = "ap-southeast-1"
  #   encrypt        = true
  #   dynamodb_table = "peerprep-terraform-locks"
  # }
}

# =============================================================================
# Provider Configuration
# =============================================================================
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "PeerPrep-Team"
    }
  }
}

# =============================================================================
# Data Sources
# =============================================================================
# Get available availability zones in the region
data "aws_availability_zones" "available" {
  state = "available"

  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

# =============================================================================
# Phase 1: VPC and Networking
# =============================================================================
module "vpc" {
  source = "./modules/vpc"

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr

  # Use first 2 availability zones for multi-AZ setup
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2)

  # Subnet CIDR blocks
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs

  # NAT Gateway configuration
  enable_nat_gateway = var.enable_nat_gateway
  single_nat_gateway = var.single_nat_gateway # Set to true for cost savings

  # DNS settings
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = var.tags
}

# =============================================================================
# Phase 1: Security Groups
# =============================================================================
module "security_groups" {
  source = "./modules/security-groups"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id

  # CIDR blocks for access control
  vpc_cidr = var.vpc_cidr

  tags = var.tags
}

# =============================================================================
# Phase 2: RDS PostgreSQL - 4 Separate Instances
# =============================================================================
# DB Subnet Group for RDS instances
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = module.vpc.private_subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-db-subnet-group"
    }
  )
}

# User Database
module "rds_user" {
  source = "./modules/rds"

  name_prefix         = "${var.project_name}-${var.environment}-user"
  vpc_id              = module.vpc.vpc_id
  database_subnet_ids = module.vpc.private_subnet_ids
  db_subnet_group_name = aws_db_subnet_group.main.name
  security_group_ids  = [module.security_groups.user_db_security_group_id]

  # Database configuration
  engine_version      = var.db_engine_version
  db_instance_class   = var.db_instance_class
  allocated_storage   = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  database_names      = ["user_db"]
  master_username     = var.db_username
  master_password     = var.db_password

  # High availability
  multi_az = var.db_multi_az

  # Backups
  backup_retention_period = var.db_backup_retention_period
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  # Safety
  deletion_protection = var.db_deletion_protection
  skip_final_snapshot = var.db_skip_final_snapshot
  apply_immediately   = false

  tags = var.tags
}

# Question Database
module "rds_question" {
  source = "./modules/rds"

  name_prefix          = "${var.project_name}-${var.environment}-question"
  vpc_id               = module.vpc.vpc_id
  database_subnet_ids  = module.vpc.private_subnet_ids
  db_subnet_group_name = aws_db_subnet_group.main.name
  security_group_ids   = [module.security_groups.question_db_security_group_id]

  # Database configuration
  engine_version        = var.db_engine_version
  db_instance_class     = var.db_instance_class
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  database_names        = ["question_db"]
  master_username       = var.db_username
  master_password       = var.db_password

  # High availability
  multi_az = var.db_multi_az

  # Backups
  backup_retention_period = var.db_backup_retention_period
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  # Safety
  deletion_protection = var.db_deletion_protection
  skip_final_snapshot = var.db_skip_final_snapshot
  apply_immediately   = false

  tags = var.tags
}

# Matching Database
module "rds_matching" {
  source = "./modules/rds"

  name_prefix          = "${var.project_name}-${var.environment}-matching"
  vpc_id               = module.vpc.vpc_id
  database_subnet_ids  = module.vpc.private_subnet_ids
  db_subnet_group_name = aws_db_subnet_group.main.name
  security_group_ids   = [module.security_groups.matching_db_security_group_id]

  # Database configuration
  engine_version        = var.db_engine_version
  db_instance_class     = var.db_instance_class
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  database_names        = ["matching_db"]
  master_username       = var.db_username
  master_password       = var.db_password

  # High availability
  multi_az = var.db_multi_az

  # Backups
  backup_retention_period = var.db_backup_retention_period
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  # Safety
  deletion_protection = var.db_deletion_protection
  skip_final_snapshot = var.db_skip_final_snapshot
  apply_immediately   = false

  tags = var.tags
}

# History Database
module "rds_history" {
  source = "./modules/rds"

  name_prefix          = "${var.project_name}-${var.environment}-history"
  vpc_id               = module.vpc.vpc_id
  database_subnet_ids  = module.vpc.private_subnet_ids
  db_subnet_group_name = aws_db_subnet_group.main.name
  security_group_ids   = [module.security_groups.history_db_security_group_id]

  # Database configuration
  engine_version        = var.db_engine_version
  db_instance_class     = var.db_instance_class
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  database_names        = ["history_db"]
  master_username       = var.db_username
  master_password       = var.db_password

  # High availability
  multi_az = var.db_multi_az

  # Backups
  backup_retention_period = var.db_backup_retention_period
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  # Safety
  deletion_protection = var.db_deletion_protection
  skip_final_snapshot = var.db_skip_final_snapshot
  apply_immediately   = false

  tags = var.tags
}

# =============================================================================
# Phase 2: ElastiCache Redis - 3 Separate Clusters
# =============================================================================
# ElastiCache Subnet Group for Redis clusters
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-redis-subnet-group"
  subnet_ids = module.vpc.private_subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-redis-subnet-group"
    }
  )
}

# Matching Redis Cluster
module "elasticache_matching" {
  source = "./modules/elasticache"

  name_prefix            = "${var.project_name}-${var.environment}-matching"
  vpc_id                 = module.vpc.vpc_id
  cache_subnet_ids       = module.vpc.private_subnet_ids
  cache_subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids     = [module.security_groups.matching_redis_security_group_id]

  # Redis configuration
  engine_version   = var.redis_engine_version
  node_type        = var.redis_node_type
  num_cache_nodes  = var.redis_num_cache_nodes

  # Maintenance and backups
  maintenance_window       = "sun:05:00-sun:06:00"
  snapshot_window          = "03:00-04:00"
  snapshot_retention_limit = var.redis_snapshot_retention_limit

  tags = var.tags
}

# Collaboration Redis Cluster (for WebSocket sessions)
module "elasticache_collaboration" {
  source = "./modules/elasticache"

  name_prefix            = "${var.project_name}-${var.environment}-collab"
  vpc_id                 = module.vpc.vpc_id
  cache_subnet_ids       = module.vpc.private_subnet_ids
  cache_subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids     = [module.security_groups.collaboration_redis_security_group_id]

  # Redis configuration
  engine_version   = var.redis_engine_version
  node_type        = var.redis_node_type
  num_cache_nodes  = var.redis_num_cache_nodes

  # Maintenance and backups
  maintenance_window       = "sun:05:00-sun:06:00"
  snapshot_window          = "03:00-04:00"
  snapshot_retention_limit = var.redis_snapshot_retention_limit

  tags = var.tags
}

# Chat Redis Cluster (for WebSocket sessions)
module "elasticache_chat" {
  source = "./modules/elasticache"

  name_prefix            = "${var.project_name}-${var.environment}-chat"
  vpc_id                 = module.vpc.vpc_id
  cache_subnet_ids       = module.vpc.private_subnet_ids
  cache_subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids     = [module.security_groups.chat_redis_security_group_id]

  # Redis configuration
  engine_version   = var.redis_engine_version
  node_type        = var.redis_node_type
  num_cache_nodes  = var.redis_num_cache_nodes

  # Maintenance and backups
  maintenance_window       = "sun:05:00-sun:06:00"
  snapshot_window          = "03:00-04:00"
  snapshot_retention_limit = var.redis_snapshot_retention_limit

  tags = var.tags
}

# =============================================================================
# Phase 3: Application Load Balancer
# =============================================================================
module "alb" {
  source = "./modules/alb"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  alb_security_group_id = module.security_groups.alb_security_group_id

  # Optional: Enable deletion protection in production
  enable_deletion_protection = var.alb_enable_deletion_protection

  # Optional: S3 bucket for access logs
  access_logs_bucket = var.alb_access_logs_bucket

  # Optional: ACM certificate ARN for HTTPS
  certificate_arn = var.alb_certificate_arn

  # CloudWatch alarm actions
  alarm_actions = var.alarm_actions

  tags = var.tags
}

# =============================================================================
# Phase 4: ECS Cluster (Commented out for Phase 1)
# =============================================================================
# module "ecs_cluster" {
#   source = "./modules/ecs-cluster"
#
#   project_name = var.project_name
#   environment  = var.environment
#
#   # Enable container insights for monitoring
#   enable_container_insights = true
#
#   tags = var.tags
# }

# =============================================================================
# Phase 5: Service Discovery (Commented out for Phase 1)
# =============================================================================
# module "service_discovery" {
#   source = "./modules/service-discovery"
#
#   project_name = var.project_name
#   environment  = var.environment
#   vpc_id       = module.vpc.vpc_id
#
#   # Service names for Cloud Map
#   services = var.service_names
#
#   tags = var.tags
# }
