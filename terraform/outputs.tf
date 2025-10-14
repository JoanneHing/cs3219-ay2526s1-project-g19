# =============================================================================
# PeerPrep AWS ECS Infrastructure - Outputs
# =============================================================================
# Key information to use after infrastructure is created
# Access with: terraform output <output_name>
# =============================================================================

# -----------------------------------------------------------------------------
# Phase 1: VPC and Networking Outputs
# -----------------------------------------------------------------------------
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = module.vpc.nat_gateway_ids
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = module.vpc.internet_gateway_id
}

# -----------------------------------------------------------------------------
# Phase 1: Security Group Outputs
# -----------------------------------------------------------------------------
output "alb_security_group_id" {
  description = "Security group ID for Application Load Balancer"
  value       = module.security_groups.alb_security_group_id
}

output "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  value       = module.security_groups.ecs_security_group_id
}

output "db_security_group_ids" {
  description = "Map of database security group IDs"
  value       = module.security_groups.db_security_group_ids
}

output "redis_security_group_ids" {
  description = "Map of Redis security group IDs"
  value       = module.security_groups.redis_security_group_ids
}

# -----------------------------------------------------------------------------
# Phase 2: RDS Outputs
# -----------------------------------------------------------------------------
output "rds_user_endpoint" {
  description = "User database endpoint"
  value       = module.rds_user.db_endpoint
  sensitive   = true
}

output "rds_question_endpoint" {
  description = "Question database endpoint"
  value       = module.rds_question.db_endpoint
  sensitive   = true
}

output "rds_matching_endpoint" {
  description = "Matching database endpoint"
  value       = module.rds_matching.db_endpoint
  sensitive   = true
}

output "rds_history_endpoint" {
  description = "History database endpoint"
  value       = module.rds_history.db_endpoint
  sensitive   = true
}

output "rds_connection_strings" {
  description = "Database connection strings for services"
  value = {
    user_db     = "postgresql://${var.db_username}:****@${module.rds_user.db_host}:${module.rds_user.db_port}/user_db"
    question_db = "postgresql://${var.db_username}:****@${module.rds_question.db_host}:${module.rds_question.db_port}/question_db"
    matching_db = "postgresql://${var.db_username}:****@${module.rds_matching.db_host}:${module.rds_matching.db_port}/matching_db"
    history_db  = "postgresql://${var.db_username}:****@${module.rds_history.db_host}:${module.rds_history.db_port}/history_db"
  }
  sensitive = true
}

# -----------------------------------------------------------------------------
# Phase 2: ElastiCache Outputs
# -----------------------------------------------------------------------------
output "redis_matching_endpoint" {
  description = "Matching Redis endpoint"
  value       = module.elasticache_matching.redis_endpoint
  sensitive   = true
}

output "redis_collaboration_endpoint" {
  description = "Collaboration Redis endpoint"
  value       = module.elasticache_collaboration.redis_endpoint
  sensitive   = true
}

output "redis_chat_endpoint" {
  description = "Chat Redis endpoint"
  value       = module.elasticache_chat.redis_endpoint
  sensitive   = true
}

output "redis_connection_strings" {
  description = "Redis connection strings for services"
  value = {
    matching      = "redis://${module.elasticache_matching.redis_endpoint}:${module.elasticache_matching.redis_port}/0"
    collaboration = "redis://${module.elasticache_collaboration.redis_endpoint}:${module.elasticache_collaboration.redis_port}/0"
    chat          = "redis://${module.elasticache_chat.redis_endpoint}:${module.elasticache_chat.redis_port}/0"
  }
  sensitive = true
}

# -----------------------------------------------------------------------------
# Phase 3: ALB Outputs (Commented out for Phase 1)
# -----------------------------------------------------------------------------
# output "alb_dns_name" {
#   description = "DNS name of the Application Load Balancer"
#   value       = module.alb.alb_dns_name
# }

# output "alb_zone_id" {
#   description = "Zone ID of the Application Load Balancer"
#   value       = module.alb.alb_zone_id
# }

# output "alb_target_group_arns" {
#   description = "Map of target group ARNs"
#   value       = module.alb.target_group_arns
# }

# -----------------------------------------------------------------------------
# Phase 4: ECS Cluster Outputs (Commented out for Phase 1)
# -----------------------------------------------------------------------------
# output "ecs_cluster_id" {
#   description = "ID of the ECS cluster"
#   value       = module.ecs_cluster.cluster_id
# }

# output "ecs_cluster_name" {
#   description = "Name of the ECS cluster"
#   value       = module.ecs_cluster.cluster_name
# }

# output "ecs_task_execution_role_arn" {
#   description = "ARN of the ECS task execution role"
#   value       = module.ecs_cluster.task_execution_role_arn
# }

# output "ecs_task_role_arn" {
#   description = "ARN of the ECS task role"
#   value       = module.ecs_cluster.task_role_arn
# }

# -----------------------------------------------------------------------------
# Phase 5: Service Discovery Outputs (Commented out for Phase 1)
# -----------------------------------------------------------------------------
# output "service_discovery_namespace_id" {
#   description = "ID of the Cloud Map namespace"
#   value       = module.service_discovery.namespace_id
# }

# output "service_discovery_namespace_name" {
#   description = "Name of the Cloud Map namespace"
#   value       = module.service_discovery.namespace_name
# }

# -----------------------------------------------------------------------------
# Summary Output (for quick reference)
# -----------------------------------------------------------------------------
output "phase_1_summary" {
  description = "Summary of Phase 1 infrastructure"
  value = {
    vpc_id          = module.vpc.vpc_id
    public_subnets  = module.vpc.public_subnet_ids
    private_subnets = module.vpc.private_subnet_ids
    security_groups_created = [
      "alb",
      "ecs",
      "db (user, question, matching, history)",
      "redis (matching, collaboration, chat)"
    ]
    next_steps = [
      "1. Run: terraform init",
      "2. Run: terraform validate",
      "3. Run: terraform plan",
      "4. Review the plan output",
      "5. Proceed to Phase 2 (RDS + ElastiCache) when ready"
    ]
  }
}
