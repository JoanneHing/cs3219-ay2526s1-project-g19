#!/bin/bash
set -euxo pipefail

# Variables
REPO_URL="${github_repo_url}"
BRANCH="${github_branch}"
DB_PASS="${db_password}"
SECRET="${secret_key}"
APP_DIR="/opt/peerprep"

# Update & install essentials
export DEBIAN_FRONTEND=noninteractive
apt-get update -y && apt-get install -y curl wget git jq ca-certificates gnupg lsb-release

# Install Docker
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list
apt-get update -y && apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable --now docker
usermod -aG docker ubuntu

# Clone repo
mkdir -p "$APP_DIR" && cd "$APP_DIR"
git clone -b "$BRANCH" "$REPO_URL" . || (git fetch origin && git checkout "$BRANCH" && git pull)

# Create production .env (matches existing .env structure)
cat > "$APP_DIR/.env" <<EOF
ENVIRONMENT=production
FRONTEND_PORT=80
QUESTION_SERVICE_PORT=8001
MATCHING_SERVICE_PORT=8002
HISTORY_SERVICE_PORT=8003
USER_SERVICE_PORT=8004
COLLABORATION_SERVICE_PORT=8005
CHAT_SERVICE_PORT=8006
MATCHING_REDIS_HOST=matching_redis
MATCHING_REDIS_PORT=6379
COLLABORATION_REDIS_HOST=collaboration_redis
COLLABORATION_REDIS_PORT=6379
CHAT_REDIS_HOST=chat_redis
CHAT_REDIS_PORT=6379
MATCHING_REDIS_URL=redis://matching_redis:6379/0
COLLABORATION_REDIS_URL=redis://collaboration_redis:6379/0
CHAT_REDIS_URL=redis://chat_redis:6379/0
QUESTION_DB_HOST=question_db
QUESTION_DB_PORT=5432
QUESTION_DB_NAME=question_db
QUESTION_DB_USER=peerprep
QUESTION_DB_PASSWORD=$DB_PASS
MATCHING_DB_HOST=matching_db
MATCHING_DB_PORT=5432
MATCHING_DB_NAME=matching_db
MATCHING_DB_USER=peerprep
MATCHING_DB_PASSWORD=$DB_PASS
HISTORY_DB_HOST=history_db
HISTORY_DB_PORT=5432
HISTORY_DB_NAME=history_db
HISTORY_DB_USER=peerprep
HISTORY_DB_PASSWORD=$DB_PASS
USER_DB_HOST=user_db
USER_DB_PORT=5432
USER_DB_NAME=user_db
USER_DB_USER=peerprep
USER_DB_PASSWORD=$DB_PASS
QUESTION_DATABASE_URL=postgresql://peerprep:$DB_PASS@question_db:5432/question_db
MATCHING_DATABASE_URL=postgresql://peerprep:$DB_PASS@matching_db:5432/matching_db
HISTORY_DATABASE_URL=postgresql://peerprep:$DB_PASS@history_db:5432/history_db
USER_DATABASE_URL=postgresql://peerprep:$DB_PASS@user_db:5432/user_db
DEBUG=false
SECRET_KEY=$SECRET
ALLOWED_HOSTS=*
USER_SERVICE_URL=http://user-service:8000
QUESTION_SERVICE_URL=http://question-service:8000
MATCHING_SERVICE_URL=http://matching-service:8000
HISTORY_SERVICE_URL=http://history-service:8000
COLLABORATION_SERVICE_URL=http://collaboration-service:8000
CHAT_SERVICE_URL=http://chat-service:8000
NODE_ENV=production
VITE_QUESTION_SERVICE_URL=/question-service-api
VITE_MATCHING_SERVICE_URL=/matching-service-api
VITE_HISTORY_SERVICE_URL=/history-service-api
VITE_USER_SERVICE_URL=/user-service-api
VITE_COLLABORATION_SERVICE_URL=/collaboration-service-api
VITE_CHAT_SERVICE_URL=/chat-service-api
NGINX_USER_SERVICE_HOST=user-service
NGINX_QUESTION_SERVICE_HOST=question-service
NGINX_MATCHING_SERVICE_HOST=matching-service
NGINX_HISTORY_SERVICE_HOST=history-service
NGINX_COLLABORATION_SERVICE_HOST=collaboration-service
NGINX_CHAT_SERVICE_HOST=chat-service
EOF

chmod 600 "$APP_DIR/.env" && chown ubuntu:ubuntu "$APP_DIR/.env"

# Start all services (databases will auto-create)
cd "$APP_DIR"
docker compose up -d --build

# Create systemd service
cat > /etc/systemd/system/peerprep.service <<UNIT
[Unit]
Description=PeerPrep Docker Compose
Requires=docker.service
After=docker.service
[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/peerprep
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=ubuntu
Group=ubuntu
[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload && systemctl enable peerprep.service

echo "Setup complete! Access at http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
