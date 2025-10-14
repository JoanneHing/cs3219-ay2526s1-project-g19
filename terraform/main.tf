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
# Phase 2: RDS PostgreSQL (Commented out for Phase 1)
# =============================================================================
# module "rds" {
#   source = "./modules/rds"
#
#   project_name          = var.project_name
#   environment           = var.environment
#   vpc_id                = module.vpc.vpc_id
#   private_subnet_ids    = module.vpc.private_subnet_ids
#   db_security_group_id  = module.security_groups.db_security_group_id
#
#   # Database configuration
#   db_instance_class     = var.db_instance_class
#   db_allocated_storage  = var.db_allocated_storage
#   db_engine_version     = var.db_engine_version
#   db_name               = var.db_name
#   db_username           = var.db_username
#   db_password           = var.db_password
#
#   # High availability
#   multi_az              = var.db_multi_az
#
#   tags = var.tags
# }

# =============================================================================
# Phase 2: ElastiCache Redis (Commented out for Phase 1)
# =============================================================================
# module "elasticache" {
#   source = "./modules/elasticache"
#
#   project_name           = var.project_name
#   environment            = var.environment
#   vpc_id                 = module.vpc.vpc_id
#   private_subnet_ids     = module.vpc.private_subnet_ids
#   redis_security_group_id = module.security_groups.redis_security_group_id
#
#   # Redis configuration
#   redis_node_type        = var.redis_node_type
#   redis_num_cache_nodes  = var.redis_num_cache_nodes
#   redis_engine_version   = var.redis_engine_version
#
#   tags = var.tags
# }

# =============================================================================
# Phase 3: Application Load Balancer (Commented out for Phase 1)
# =============================================================================
# module "alb" {
#   source = "./modules/alb"
#
#   project_name         = var.project_name
#   environment          = var.environment
#   vpc_id               = module.vpc.vpc_id
#   public_subnet_ids    = module.vpc.public_subnet_ids
#   alb_security_group_id = module.security_groups.alb_security_group_id
#
#   # Service names for target groups
#   services = var.service_names
#
#   tags = var.tags
# }

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
