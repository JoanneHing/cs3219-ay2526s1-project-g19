#!/bin/bash
# =============================================================================
# Upload secrets/.env to AWS SSM Parameter Store
# =============================================================================
# Usage: ./scripts/setup-ssm-secrets.sh
# =============================================================================

set -euo pipefail

# Configuration
SECRETS_DIR="${1:-../secrets}"
ENV_FILE="${SECRETS_DIR}/.env"
AWS_REGION="${AWS_REGION:-us-east-1}"
SSM_BASE_PATH="/peerprep/ec2-prod"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Validation
# =============================================================================

log_info "Uploading secrets to AWS SSM Parameter Store..."

if [[ ! -f "$ENV_FILE" ]]; then
    log_error "File not found: $ENV_FILE"
    echo ""
    echo "Create the file first:"
    echo "  mkdir -p secrets"
    echo "  cp terraform_ec2/.env.secrets.template secrets/.env"
    echo "  # Edit secrets/.env with your values"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    log_error "AWS CLI not installed"
    exit 1
fi

if ! aws sts get-caller-identity --region "$AWS_REGION" &> /dev/null; then
    log_error "AWS credentials not configured"
    exit 1
fi

log_success "Found: $ENV_FILE"
log_info "Region: $AWS_REGION"
log_info "SSM Path: $SSM_BASE_PATH"
echo ""

# =============================================================================
# Upload entire .env file as single parameter
# =============================================================================

log_info "Uploading complete .env file..."

SSM_PARAM_NAME="${SSM_BASE_PATH}/ENV_FILE"

if aws ssm put-parameter \
    --name "$SSM_PARAM_NAME" \
    --value "file://$ENV_FILE" \
    --type "SecureString" \
    --region "$AWS_REGION" \
    --overwrite \
    --tags "Key=Project,Value=peerprep" "Key=Environment,Value=ec2-prod" \
    &> /dev/null; then
    log_success "✓ Uploaded to: $SSM_PARAM_NAME"
else
    log_error "Failed to upload to SSM"
    exit 1
fi

echo ""
log_success "✓ Upload complete!"
echo ""
echo "Next steps:"
echo "  1. Enable SSM in terraform.tfvars:"
echo "     use_ssm_secrets = true"
echo ""
echo "  2. Deploy:"
echo "     cd terraform_ec2"
echo "     terraform apply"
echo ""
echo "To view uploaded secrets:"
echo "  aws ssm get-parameter --name $SSM_PARAM_NAME --region $AWS_REGION --with-decryption --query 'Parameter.Value' --output text"
echo ""
