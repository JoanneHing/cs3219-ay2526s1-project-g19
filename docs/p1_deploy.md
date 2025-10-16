# Service Containerization (Implementation & Deployment Decisions)

Some of these decisions depend on the chosen nice-to-have categories, but the current plan already covers the must-have scope below.

## Chosen Approach to Containerize Must-Have Services

All seven must-have services (frontend, user, question, matching, history, collaboration, chat) keep a dedicated Dockerfile and standalone `docker-compose.yml`. The root-level `docker-compose.yml` simply includes each sub-service so local developers can spin up the entire stack, while `docker-compose.prod.yml` removes the local Postgres/Redis sidecars and expects Terraform-managed RDS/ElastiCache instead. Backends use slim Python bases with an entrypoint that blocks on dependencies, runs migrations, and exposes `/health`. The frontend builds under Node 22 and serves static assets out of an Nginx stage.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'14px'}}}%%
graph LR
  subgraph ServiceRepos["Service Repos"]
    FE["Frontend"]
    US["User Svc"]
    QS["Question Svc"]
    MS["Matching Svc"]
    HS["History Svc"]
    CS["Collab Svc"]
    CH["Chat Svc"]
  end

  FE --> FE_IMG["Frontend image<br/>node:22-slim → nginx:alpine"]
  US --> US_IMG["User image<br/>python:3.10-slim"]
  QS --> QS_IMG["Question image<br/>python:3.10-slim"]
  MS --> MS_IMG["Matching image<br/>python:3.13-slim"]
  HS --> HS_IMG["History image<br/>python:3.10-slim"]
  CS --> CS_IMG["Collab image<br/>python:3.10-slim"]
  CH --> CH_IMG["Chat image<br/>python:3.10-slim"]

  FE_IMG --> Compose["docker-compose.yml<br/>include tree"]
  US_IMG --> Compose
  QS_IMG --> Compose
  MS_IMG --> Compose
  HS_IMG --> Compose
  CS_IMG --> Compose
  CH_IMG --> Compose
  Compose --> DevStack["Local dev stack<br/>with hot-reload"]
  Compose --> ProdOverlay["docker-compose<br/>.prod.yml"]
  ProdOverlay --> Terraform["ECS task defs<br/>Terraform"]
  Terraform --> Fargate["ECS Fargate<br/>RDS/ElastiCache"]

  classDef wider padding:10px
  class FE,US,QS,MS,HS,CS,CH,FE_IMG,US_IMG,QS_IMG,MS_IMG,HS_IMG,CS_IMG,CH_IMG,Compose,DevStack,ProdOverlay,Terraform,Fargate wider
```

## Deployment Workflow and CI/CD Considerations

Operators follow scripted steps today: validate prerequisites, deploy infrastructure, build and push ECR images, run migrations, verify the stack, and optionally force ECS to refresh tasks. `DEPLOY.sh` chains those scripts; the next increment is to encode the same stages inside GitHub Actions so build » test » scan » push is gated automatically before a Terraform apply and production deploy.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'14px'}}}%%
flowchart TD
  start([Kick off DEPLOY.sh]) --> checklist["Pre-deployment check<br/>Tools & creds OK?"]
  checklist -->|pass| tf["Deploy infrastructure<br/>terraform init/plan/apply"]
  tf --> build["Build & push images<br/>docker build → ECR"]
  build --> migrate["Run migrations<br/>Apply Django migrations"]
  migrate --> verify["Verify deployment<br/>Smoke tests"]
  verify --> refresh["Force service update<br/>New ECS deployment"]
  refresh --> done([Deployment complete])
  checklist -->|fail| stop1([Fix issues, rerun])
  tf -->|plan rejected| stop2([Abort until reviewed])

  classDef wider padding:10px
  class checklist,tf,build,migrate,verify,refresh wider
```

## Alignment with Scalability and Production Readiness

Terraform provisions an ECS Fargate cluster, Cloud Map service discovery, an ALB with path-based routing, and autoscaling policies anchored on CPU, memory, and ALB request counts. Each must-have service defaults to two tasks, leaves 50% of capacity healthy during deploys (max 200%), and uses ECS’ deployment circuit breaker so failed rollouts revert automatically. Managed RDS/Redis back the stateful pieces, while compose parity ensures dev/prod behavior matches.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'14px'}}}%%
graph TD
  ALB["ALB<br/>path routing"] --> UserTG["User TG"]
  ALB --> QuestionTG["Question TG"]
  ALB --> MatchingTG["Matching TG"]
  ALB --> HistoryTG["History TG"]
  ALB --> CollabTG["Collab TG"]
  ALB --> ChatTG["Chat TG"]
  ALB --> FrontendTG["Frontend TG"]

  UserTG --> UserECS["ECS User<br/>2 tasks"]
  QuestionTG --> QuestionECS["ECS Question"]
  MatchingTG --> MatchingECS["ECS Matching"]
  HistoryTG --> HistoryECS["ECS History"]
  CollabTG --> CollabECS["ECS Collab"]
  ChatTG --> ChatECS["ECS Chat"]
  FrontendTG --> FrontendECS["ECS Frontend"]

  UserECS --> RDSUser["RDS PG<br/>user_db"]
  QuestionECS --> RDSQuestion["RDS PG<br/>question_db"]
  MatchingECS --> RDSMatching["RDS PG<br/>matching_db"]
  HistoryECS --> RDSHistory["RDS PG<br/>history_db"]
  MatchingECS --> RedisMatching["Redis<br/>matching"]
  CollabECS --> RedisCollab["Redis<br/>collab"]
  ChatECS --> RedisChat["Redis<br/>chat"]

  subgraph AutoscalingPolicies["Autoscaling"]
    CPU["CPU"]
    MEM["Memory"]
    REQ["Requests"]
  end
  AutoscalingPolicies --> UserECS
  AutoscalingPolicies --> QuestionECS
  AutoscalingPolicies --> MatchingECS
  AutoscalingPolicies --> HistoryECS
  AutoscalingPolicies --> CollabECS
  AutoscalingPolicies --> ChatECS
  AutoscalingPolicies --> FrontendECS

  CloudMap["Cloud Map<br/>DNS discovery"] --> UserECS
  CloudMap --> QuestionECS
  CloudMap --> MatchingECS
  CloudMap --> HistoryECS
  CloudMap --> CollabECS
  CloudMap --> ChatECS
  CloudMap --> FrontendECS

  classDef wider padding:10px
  class ALB,UserTG,QuestionTG,MatchingTG,HistoryTG,CollabTG,ChatTG,FrontendTG,UserECS,QuestionECS,MatchingECS,HistoryECS,CollabECS,ChatECS,FrontendECS,RDSUser,RDSQuestion,RDSMatching,RDSHistory,RedisMatching,RedisCollab,RedisChat,CloudMap wider
```

## Implementation Tech Stack

Backends run Django (user/question/history) or FastAPI/Socket.IO (matching/collaboration/chat) on slim Python images and install dependencies via `pip`; the frontend builds with Vite under Node 22, then serves static assets through Nginx with runtime `envsubst`. `01-build-and-push-images.sh` enforces `--platform linux/amd64`, clears caches, and tags both local and ECR images. Image/security scanning is currently manual—adding Trivy or ECR scans plus Git SHA tags is the next increment.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'14px'}}}%%
graph LR
  subgraph FrontendStack["Frontend"]
    FEStack["Vite + React<br/>Node → Nginx"]
    npmci["npm ci"]
  end

  subgraph DjangoServices["Django"]
    UserSvc["User<br/>Python 3.10"]
    QuestionSvc["Question<br/>Python 3.10"]
    HistorySvc["History<br/>Python 3.10"]
    DjangoEntrypoint["migrate +<br/>collectstatic"]
  end

  subgraph FastAPISocket["FastAPI"]
    MatchingSvc["Matching<br/>Python 3.13"]
    CollabSvc["Collab<br/>Python 3.10"]
    ChatSvc["Chat<br/>Python 3.10"]
    FastAPIEntrypoint["uvicorn<br/>start"]
  end

  npmci --> FEStack --> ImageBuild["Multi-stage<br/>build"]
  UserSvc --> DjangoEntrypoint
  QuestionSvc --> DjangoEntrypoint
  HistorySvc --> DjangoEntrypoint
  DjangoEntrypoint --> ImageBuild
  MatchingSvc --> FastAPIEntrypoint
  CollabSvc --> FastAPIEntrypoint
  ChatSvc --> FastAPIEntrypoint
  FastAPIEntrypoint --> ImageBuild
  ImageBuild --> ECRTag["ECR :latest<br/>+ Git SHA"]
  ECRTag -. future .-> Trivy["Security<br/>scan"]

  classDef wider padding:10px
  class FEStack,npmci,UserSvc,QuestionSvc,HistorySvc,DjangoEntrypoint,MatchingSvc,CollabSvc,ChatSvc,FastAPIEntrypoint,ImageBuild,ECRTag,Trivy wider
```

## Configuration and Secrets

Local developers copy `.env.sample`/`.env.prod.sample` into `.env`/`.env.prod`, which docker-compose reads. Terraform consumes `terraform.tfvars` (holding non-committed values like `db_password`, `secret_key`) and injects them into ECS task definitions as environment variables. `ENVIRONMENT_VARIABLES.md` documents the full matrix. Secrets live in Terraform variables for now; the ECS execution role already has `secretsmanager:GetSecretValue`, so we can later migrate to AWS Secrets Manager/SSM via the module’s `secrets` field.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'14px'}}}%%
graph TD
  Samples[".env samples"] --> LocalEnv[".env files"]
  LocalEnv --> ComposeEnv["docker-compose"]

  TFVars["terraform.tfvars<br/>secrets"] --> TerraformApply["terraform apply"]
  TerraformApply --> TaskDefs["ECS task defs<br/>env vars"]
  TaskDefs --> FargateTasks["Fargate tasks"]

  FargateTasks --> Services["Services"]
  Services --> Usage["Load config"]

  SecretsMgr["Secrets Mgr"] -. planned .-> TaskDefs

  classDef wider padding:10px
  class Samples,LocalEnv,ComposeEnv,TFVars,TerraformApply,TaskDefs,FargateTasks,Services,Usage,SecretsMgr wider
```

## Networking and Ingress

Compose attaches every container to a shared bridge network plus service-specific networks for their databases/Redis (only necessary ports exposed). In AWS, Terraform builds VPC subnets, an ALB with path-based listener rules, and Cloud Map DNS so backend services call each other via `<service>.peerprep-prod.local`. The frontend Nginx template proxies the `/something-service-api` paths to the internal hostnames, and WebSocket workloads use ALB cookie stickiness.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'14px'}}}%%
graph LR
  subgraph LocalCompose["Local"]
    FrontendC["Frontend<br/>:80"] --> SharedNet["shared net"]
    UserC["User<br/>:8001"] --> SharedNet
    QuestionC["Question<br/>:8002"] --> SharedNet
    MatchingC["Matching<br/>:8003"] --> SharedNet
    HistoryC["History<br/>:8004"] --> SharedNet
    CollabC["Collab<br/>:8005"] --> SharedNet
    ChatC["Chat<br/>:8006"] --> SharedNet
  end

  subgraph AWSVPC["AWS VPC"]
    ALB2["ALB"] -->|"/user-*"| UserTG
    ALB2 -->|"/question-*"| QuestionTG
    ALB2 -->|"/matching-*"| MatchingTG
    ALB2 -->|"/history-*"| HistoryTG
    ALB2 -->|"/collab-*"| CollabTG
    ALB2 -->|"/chat-*"| ChatTG
    ALB2 -->|"/"| FrontendTG

    UserTG --> UserTask["ECS User"]
    QuestionTG --> QuestionTask["ECS Question"]
    MatchingTG --> MatchingTask["ECS Matching"]
    HistoryTG --> HistoryTask["ECS History"]
    CollabTG --> CollabTask["ECS Collab<br/>sticky"]
    ChatTG --> ChatTask["ECS Chat<br/>sticky"]
    FrontendTG --> FrontendTask["ECS Frontend"]
  end

  CloudMap["Cloud Map<br/>DNS"] --> UserTask
  CloudMap --> QuestionTask
  CloudMap --> MatchingTask
  CloudMap --> HistoryTask
  CloudMap --> CollabTask
  CloudMap --> ChatTask
  CloudMap --> FrontendTask

  classDef wider padding:10px
  class FrontendC,UserC,QuestionC,MatchingC,HistoryC,CollabC,ChatC,SharedNet,ALB2,UserTG,QuestionTG,MatchingTG,HistoryTG,CollabTG,ChatTG,FrontendTG,UserTask,QuestionTask,MatchingTask,HistoryTask,CollabTask,ChatTask,FrontendTask,CloudMap wider
```

## CI/CD and Rollout Strategy

The documented flow covers build → migrate → verify. When scripts run manually, Terraform plan/apply pauses for approval, then ECS performs rolling updates (min healthy 50%, max 200%) with the circuit breaker enabled. `05-force-service-update.sh` can trigger a new deployment after fresh images land. Automating the same sequence inside CI/CD will let us gate dev → staging → prod promotions behind automated tests and change approvals.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'14px'}}}%%
stateDiagram-v2
  [*] --> DevBranch
  DevBranch --> CI_Build: PR push
  CI_Build --> CI_Test
  CI_Test --> CI_Scan
  CI_Scan --> MainMerge: Merge to main
  MainMerge --> ECR_Push: Build and push images
  ECR_Push --> TerraformPlan: Manual approval
  TerraformPlan --> TerraformApply
  TerraformApply --> Migrations
  Migrations --> ECSRolling
  ECSRolling --> SmokeTests: Success
  SmokeTests --> ProdLive
  ProdLive --> [*]
  ECSRolling --> Rollback: Failure detected
  Rollback --> ProdLive

  note right of ECSRolling
    ECS rolling deploy
    minHealthy=50%
    max=200%
    circuit breaker enabled
  end note

  note right of SmokeTests
    04-verify-deployment.sh
  end note
```

## Observability, Health Checks, and Alerts

`ADD_HEALTH_ENDPOINTS.md` describes the `/health` endpoints every service should expose. Those endpoints power docker-compose health checks, ALB target group probes, and ECS task health commands. Logs flow into CloudWatch (`/ecs/peerprep-prod`) with Container Insights enabled. `04-verify-deployment.sh` performs post-deploy smoke tests; operators can tail logs or curl `/health` through the ALB. Next steps are to harden automated health dashboards and alerting on CPU/memory/request metrics, and layer in structured logging or tracing once service-level objectives are defined.

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'14px'}}}%%
graph LR
  HealthEP["/health"] --> ComposeHC["Compose<br/>checks"]
  HealthEP --> ALBHC["ALB health"]
  HealthEP --> ECSHC["ECS health"]

  ECSHC --> ECS["ECS"]
  ECS --> Logs["CloudWatch<br/>Logs"]
  ECS --> Metrics["CloudWatch<br/>Metrics"]
  Metrics -. roadmap .-> Alerts["Dashboards"]

  VerifyScript["Verify script"] --> ALBHC
  VerifyScript --> Metrics
  VerifyScript --> Logs

  Operator["Operator"] -->|"tail"| Logs
  Operator -->|"curl"| HealthEP

  classDef wider padding:10px
  class HealthEP,ComposeHC,ALBHC,ECSHC,ECS,Logs,Metrics,Alerts,VerifyScript,Operator wider
```
