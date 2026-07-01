#!/bin/bash
# Create Kubernetes secrets for local development from .env file
# Usage: ./infra/k8s/create-local-secrets.sh [namespace]

set -e

# Default namespace
NAMESPACE=${1:-ecole-local}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Creating Kubernetes Secrets for Local Development ===${NC}"
echo -e "${YELLOW}Namespace: $NAMESPACE${NC}"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

# Load environment variables — prefer Doppler, fallback to .env
if command -v doppler &> /dev/null && doppler me &> /dev/null; then
    echo -e "${GREEN}Loading environment variables from Doppler (config: dev)${NC}"
    DOPPLER_TMP=$(mktemp)
    doppler secrets download --config dev --no-file --format env > "$DOPPLER_TMP"
    export $(grep -v '^#' "$DOPPLER_TMP" | xargs)
    rm -f "$DOPPLER_TMP"
elif [ -f .env ]; then
    echo -e "${GREEN}Loading environment variables from .env${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}Warning: No .env file found and Doppler not configured${NC}"
    echo "Using default values for secrets..."
fi

# Set default values if not set
DATABASE_URL="${DATABASE_URL:-postgresql://ecole:ecole@host.docker.internal:5432/ecole_platform}"
REDIS_URL="${REDIS_URL:-redis://host.docker.internal:6379/0}"
JWT_SECRET_KEY="${JWT_SECRET_KEY:-local-dev-secret-key-change-in-production}"
SMTP_PASSWORD="${SMTP_PASSWORD:-}"

# Create namespace if it doesn't exist
echo -e "${GREEN}Ensuring namespace exists: $NAMESPACE${NC}"
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Create database URL secret
echo -e "${GREEN}Creating ecole-database-url secret...${NC}"
kubectl create secret generic ecole-database-url \
    -n "$NAMESPACE" \
    --from-literal=DATABASE_URL="$DATABASE_URL" \
    --dry-run=client -o yaml | kubectl apply -f -

# Create Redis URL secret
echo -e "${GREEN}Creating ecole-redis-url secret...${NC}"
kubectl create secret generic ecole-redis-url \
    -n "$NAMESPACE" \
    --from-literal=REDIS_URL="$REDIS_URL" \
    --dry-run=client -o yaml | kubectl apply -f -

# Create JWT secret
echo -e "${GREEN}Creating ecole-jwt-secret secret...${NC}"
kubectl create secret generic ecole-jwt-secret \
    -n "$NAMESPACE" \
    --from-literal=JWT_SECRET_KEY="$JWT_SECRET_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

# Create SMTP password secret
echo -e "${GREEN}Creating ecole-smtp-password secret...${NC}"
kubectl create secret generic ecole-smtp-password \
    -n "$NAMESPACE" \
    --from-literal=SMTP_PASSWORD="$SMTP_PASSWORD" \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}=== Secrets Created Successfully ===${NC}"
echo -e "${YELLOW}To view secrets:${NC}"
echo "  kubectl get secrets -n $NAMESPACE"
echo ""
echo -e "${YELLOW}To view secret values (base64 decoded):${NC}"
echo "  kubectl get secret ecole-database-url -n $NAMESPACE -o jsonpath='{.data.DATABASE_URL}' | base64 -d"
echo "  kubectl get secret ecole-redis-url -n $NAMESPACE -o jsonpath='{.data.REDIS_URL}' | base64 -d"
echo "  kubectl get secret ecole-jwt-secret -n $NAMESPACE -o jsonpath='{.data.JWT_SECRET_KEY}' | base64 -d"
echo ""
echo -e "${YELLOW}To delete secrets:${NC}"
echo "  kubectl delete secret ecole-database-url ecole-redis-url ecole-jwt-secret ecole-smtp-password -n $NAMESPACE"
