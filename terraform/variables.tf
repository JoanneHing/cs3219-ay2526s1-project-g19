# =============================================================================
# PeerPrep AWS ECS Infrastructure - Variables
# =============================================================================
# All configurable parameters for the infrastructure
# Override these values in terraform.tfvars
# =============================================================================

# -----------------------------------------------------------------------------
# Global Settings
# -----------------------------------------------------------------------------
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "peerprep"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# VPC and Networking Configuration
# -----------------------------------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (must match number of AZs)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (must match number of AZs)"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway for all private subnets (cost savings)"
  type        = bool
  default     = true # Set to false for high availability (one NAT per AZ)
}

# -----------------------------------------------------------------------------
# RDS PostgreSQL Configuration (Phase 2)
# -----------------------------------------------------------------------------
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro" # Eligible for free tier
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "db_name" {
  description = "Initial database name"
  type        = string
  default     = "peerprep"
}

variable "db_username" {
  description = "Master username for RDS"
  type        = string
  default     = "peerprep_admin"
  sensitive   = true
}

variable "db_password" {
  description = "Master password for RDS"
  type        = string
  sensitive   = true
  default     = "" # Must be set in terraform.tfvars or via environment variable
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment for high availability"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# ElastiCache Redis Configuration (Phase 2)
# -----------------------------------------------------------------------------
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes (use 2+ for high availability)"
  type        = number
  default     = 2
}

variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

# -----------------------------------------------------------------------------
# ECS Service Configuration (Phase 4)
# -----------------------------------------------------------------------------
variable "service_names" {
  description = "List of microservice names"
  type        = list(string)
  default = [
    "user-service",
    "question-service",
    "matching-service",
    "history-service",
    "collaboration-service",
    "chat-service",
    "frontend"
  ]
}

variable "ecs_task_cpu" {
  description = "CPU units for ECS tasks (256 = 0.25 vCPU, 512 = 0.5 vCPU, 1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "Memory for ECS tasks in MB"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "Desired number of tasks per service"
  type        = number
  default     = 2
}

variable "ecs_min_capacity" {
  description = "Minimum number of tasks for auto-scaling"
  type        = number
  default     = 2
}

variable "ecs_max_capacity" {
  description = "Maximum number of tasks for auto-scaling"
  type        = number
  default     = 10
}

# -----------------------------------------------------------------------------
# Container Image Configuration (Phase 4)
# -----------------------------------------------------------------------------
variable "container_images" {
  description = "Map of service names to container image URIs"
  type        = map(string)
  default     = {}
  # Example:
  # {
  #   "user-service" = "123456789012.dkr.ecr.ap-southeast-1.amazonaws.com/peerprep-user-service:latest"
  #   "question-service" = "123456789012.dkr.ecr.ap-southeast-1.amazonaws.com/peerprep-question-service:latest"
  # }
}

# -----------------------------------------------------------------------------
# Auto-scaling Configuration (Phase 6)
# -----------------------------------------------------------------------------
variable "autoscaling_cpu_target" {
  description = "Target CPU utilization percentage for auto-scaling"
  type        = number
  default     = 70
}

variable "autoscaling_memory_target" {
  description = "Target memory utilization percentage for auto-scaling"
  type        = number
  default     = 80
}

variable "autoscaling_requests_target" {
  description = "Target request count per container for auto-scaling"
  type        = number
  default     = 1000
}
