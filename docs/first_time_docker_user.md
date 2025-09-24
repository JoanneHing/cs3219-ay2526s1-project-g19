Quick Start
# 1. Clone and enter project
git clone <repo-url>
cd cs3219-project

# 2. Start Docker Desktop
open -a Docker

# 3. Copy environment file
cp .env.local.sample .env.local

# 4. Run everything

## Build 
docker-compose up --build

## Access Your Services

Frontend: http://localhost:5173
Question API: http://localhost:8001
Matching API: http://localhost:8002
Collaboration API: http://localhost:8003

## Daily Development

### Start services:
docker-compose up -d
### Stop services:
docker-compose down
### View logs:
docker-compose logs -f
### Clean restart:
docker-compose down -v
docker-compose up --build


## Working on Specific Services
### Frontend developer (fastest):
cd frontend
npm run dev

###  Backend developer: Only restart your service
docker-compose up question_service --build

# Troubleshooting

## Check what's running
docker ps

## Clean everything
docker system prune -f
docker-compose down -v
docker-compose up --build

That's it. Start with the Quick Start section, then use Daily Development commands.Retry