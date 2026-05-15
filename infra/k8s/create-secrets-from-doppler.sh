#!/bin/bash
# Create Kubernetes secrets from Doppler for local development
# Usage: ./infra/k8s/create-secrets-from-doppler.sh [namespace] [doppler-config]
#
# Examples:
#   ./infra/k8s/create-secrets-from-doppler.sh ecole-local dev
#   ./infra/k8s/create-secrets-from-doppler.sh ecole-local stg_main

set -e

# Default values
NAMESPACE=${1:-ecole-local}
DOPPLER_CONFIG=${2:-dev}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Creating Kubernetes Secrets from Doppler ===${NC}"
echo -e "${YELLOW}Namespace: $NAMESPACE${NC}"
echo -e "${YELLOW}Doppler config: $DOPPLER_CONFIG${NC}"

# Check if doppler is installed
if ! command -v doppler &> /dev/null; then
    echo -e "${RED}Error: Doppler CLI is not installed${NC}"
    echo "Install it with: brew install dopplerhq/cli/doppler"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

# Create namespace if it doesn't exist
echo -e "${GREEN}Ensuring namespace exists: $NAMESPACE${NC}"
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Download secrets from Doppler
echo -e "${GREEN}Downloading secrets from Doppler (config: $DOPPLER_CONFIG)...${NC}"
TMP_ENV=$(mktemp)
trap "rm -f $TMP_ENV" EXIT

doppler secrets download --config "$DOPPLER_CONFIG" --no-file --format env > "$TMP_ENV"

# Load variables
export $(grep -v '^#' "$TMP_ENV" | xargs)

# Create database URL secret
echo -e "${GREEN}Creating ecole-database-url secret...${NC}"
kubectl create secret generic ecole-database-url \
    -n "$NAMESPACE" \
    --from-literal=DATABASE_URL="${DATABASE_URL:-postgresql://ecole:ecole@host.docker.internal:5432/ecole_platform}" \
    --dry-run=client -o yaml | kubectl apply -f -

# Create Redis URL secret
echo -e "${GREEN}Creating ecole-redis-url secret...${NC}"
kubectl create secret generic ecole-redis-url \
    -n "$NAMESPACE" \
    --from-literal=REDIS_URL="${REDIS_URL:-redis://host.docker.internal:6379/0}" \
    --dry-run=client -o yaml | kubectl apply -f -

# Create JWT secret
echo -e "${GREEN}Creating ecole-jwt-secret secret...${NC}"
kubectl create secret generic ecole-jwt-secret \
    -n "$NAMESPACE" \
    --from-literal=JWT_SECRET_KEY="${JWT_SECRET_KEY:-local-dev-secret-key-change-in-production}" \
    --dry-run=client -o yaml | kubectl apply -f -

# Create SMTP password secret
echo -e "${GREEN}Creating ecole-smtp-password secret...${NC}"
kubectl create secret generic ecole-smtp-password \
    -n "$NAMESPACE" \
    --from-literal=SMTP_PASSWORD="${SMTP_PASSWORD:-}" \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}=== Secrets Created Successfully ===${NC}"
echo -e "${YELLOW}To view secrets:${NC}"
echo "  kubectl get secrets -n $NAMESPACE"
echo ""
echo -e "${YELLOW}To delete secrets:${NC}"
echo "  kubectl delete secret ecole-database-url ecole-redis-url ecole-jwt-secret ecole-smtp-password -n $NAMESPACE"
