# Service Containerization (Implementation & Deployment Decisions)
Some of these decisions would depend on choice of nice-to have category(ies)

# Chosen approach to containerize must have services.
- All seven must-have services (frontend plus user, question, matching, history, collaboration, and chat) ship dedicated Dockerfiles and docker-compose file within their service folders and are orchestrated through the root `docker-compose.yml` include tree. 

- Local development keeps hot-reload volume mounts, while production builds rely on the multi-stage images 
    (
        `frontend/Dockerfile` compiles with `node:22-slim` before serving from `nginx:alpine`; 
        backend images use slim Python bases with entrypoints that run migrations and expose `/health`
    ). 
    Each service compose file declares its own Postgres or Redis dependency and attaches to the shared network; the production overlay (`docker-compose.prod.yml`) removes those sidecars so Terraform-provisioned RDS and ElastiCache instances can be used instead.

# Deployment workflow and CI/CD considerations.
The deployment flow is scripted end-to-end: 

- `00-pre-deployment-checklist.sh` validates tooling, 
- `02-deploy-infrastructure.sh` plans/applies Terraform, 
- `01-build-and-push-images.sh` forces linux/amd64 image builds and tags them for ECR, 
- `03-run-migrations.sh` applies Django migrations via the freshly provisioned endpoints, 
- `04-verify-deployment.sh` runs post-deploy smoke checks, and 
- `05-force-service-update.sh` triggers rolling updates after new images land. 
- `DEPLOY.sh` stitches the steps for operators today; 

The next refinement is to mirror those stages in GitHub Actions 
--> so build » test » scan » push gates on a reviewed Terraform plan before promoting to staging/production.

# Alignment with scalability and production readiness.
Terraform provisions an ECS Fargate cluster with 
- Cloud Map service discovery, 
- path-based routing through an Application Load Balancer,and 
- auto-scaling policies based on CPU, memory, and ALB request count. 
    - Default desired counts are two tasks per must-have service, deployment settings (50% minimum healthy, 200% max) 
- plus the circuit breaker provide safe rolling updates, 
- and Redis/Postgres dependencies live on managed ElastiCache and RDS instances. 



# Implementation tech stack: 
language/runtime versions, package manager, framework; base image choice; Dockerfile strategy, dependency/security scanning, image tagging/versioning.

## Language
- Backend services (user, question, history) run Django on `python:3.10-slim`, 
- matching runs FastAPI/uvicorn on `python:3.13-slim`, and 
- collaboration/chat expose Socket.IO and aiohttp workers on `python:3.10-slim`; 

## Package Manager
- all install dependencies through `pip` with `requirements.txt`. 
- The frontend builds with Vite under `node:22-slim` 
- and serves static assets via `nginx:alpine` with runtime `envsubst`. 
- `01-build-and-push-images.sh` enforces `--platform linux/amd64` for ECS compatibility, the entrypoint scripts wait for databases and run migrations, and caches are cleared to shrink layers. 
- Image/security scanning is still manual—next action is to wire in `trivy`/ECR scanning during the build step 
-- and adopt commit SHA tags alongside the existing `latest` tag to improve traceability.

## Configuration & secrets: env vars, secret management (e.g., SSM/Secrets Manager/K8s Secrets)
- Local docker-compose runs from `.env` / `.env.prod` files copied from the provided samples, 
- while Terraform injects runtime configuration (database URLs, service discovery endpoints, `SECRET_KEY`, Redis hosts) into each ECS task definition using variables sourced from `terraform.tfvars`. `ENVIRONMENT_VARIABLES.md` tracks the full matrix. 
- Sensitive values currently live in Terraform variables (kept out of git); 

- the ECS execution role already has `secretsmanager:GetSecretValue`, 
- so the plan is to move database passwords and the Django secret key into AWS Secrets Manager/SSM and map them through the module’s `secrets` block once provisioned.

## Networking & ingress: service-to-service comms, ingress/controller choice, ports, API gateway/ingress rules.
- Docker-compose attaches every container to `shared_network` plus a service-specific network for its Postgres/Redis sidecars, exposing only the required host ports (frontend on 80/5173, backends on 8000-series). 
- In AWS, Terraform builds a VPC with public subnets for the ALB, private subnets for ECS tasks, Cloud Map DNS (`<service>.peerprep-prod.local`) for east-west traffic, and listener rules that map `/user-service-api/*` and similar paths to the correct target groups. 
- The frontend nginx template proxies those prefixes to the internal hostnames, and WebSocket services benefit from ALB cookie stickiness.

## Cl/CD & rollout: pipeline stages (build »test>scan>push>deploy),promotion flow (dev»staging→prod), rollout strategy (rolling/blue green/canary), rollback plan.

- The scripted flow (see `DEPLOYMENT_GUIDE.md`) covers build → migrate → verify: 
run the pre-checks, terraform plan/apply (with a manual confirmation), build and push images, execute migrations against RDS, then verify ALB/target health. 

- ECS services use rolling deployments with min/max healthy settings plus a deployment circuit breaker for fast rollback, and `05-force-service-update.sh` offers a controlled redeploy trigger after publishing new images. 

```
• In our context the “circuit breaker” is the ECS deployment safeguard configured in modules/ecs-service/main.tf:143. When deployment_circuit_breaker { enable = true, rollback = true } is set, ECS watches each rolling deployment; if the new task set can’t reach steady state (for example, health checks fail or tasks crash) it automatically stops the rollout and reverts to the previous healthy task definition instead of leaving the service in a broken or partial state.
```

-  Rollbacks today are handled by redeploying the prior task definition or scaling down the new revision; 
-  codifying these scripts in CI will let us gate dev → staging → prod promotions behind automated tests and change approvals.

## 5. Observability: logs/metrics/traces, health checks (liveness/readiness),
dashboards & alerts.
- Container health expectations are documented in `ADD_HEALTH_ENDPOINTS.md` (each service should expose `/health`), and those endpoints back the docker-compose health checks, ALB target probes, and ECS task health configuration. 
- Terraform enables CloudWatch Container Insights and ships logs to `/ecs/peerprep-prod`, while `04-verify-deployment.sh` performs smoke tests after each release and operators can tail `aws logs tail /ecs/peerprep-prod --follow`. 
- Follow-up work is to pin CloudWatch alarms/dashboards on the existing CPU, memory, and request metrics and, longer-term, introduce structured logging or tracing once service-level objectives are defined.

