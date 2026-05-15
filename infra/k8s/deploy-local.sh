#!/bin/bash
# Deploy École Platform to local Kubernetes (Kind recommended)
# Usage: ./infra/k8s/deploy-local.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== École Platform Local Kubernetes Deployment ===${NC}"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    echo "Install it with: brew install kubectl"
    exit 1
fi

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: helm is not installed${NC}"
    echo "Install it with: brew install helm"
    exit 1
fi

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo -e "${YELLOW}Kind not found. Installing...${NC}"
    brew install kind
fi

# Check current context
CURRENT_CONTEXT=$(kubectl config current-context)
echo -e "${YELLOW}Current Kubernetes context: $CURRENT_CONTEXT${NC}"

# Determine if using Kind
USE_KIND=false
if [[ "$CURRENT_CONTEXT" == "kind-"* ]]; then
    USE_KIND=true
    CLUSTER_NAME=$(echo "$CURRENT_CONTEXT" | sed 's/kind-//')
    echo -e "${GREEN}Using Kind cluster: $CLUSTER_NAME${NC}"
else
    echo -e "${YELLOW}Warning: Not using Kind. Local images may not work with Docker Desktop.${NC}"
    echo -e "${YELLOW}Consider using Kind for local development:${NC}"
    echo -e "${YELLOW}  kind create cluster --name ecole-dev${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
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
fi

# Build local Docker images
echo -e "${GREEN}Building local Docker images...${NC}"
docker build -t ecole-platform-backend:local ./backend
docker build -t ecole-platform-web:local ./web

# Load images into Kind (if using Kind)
if [ "$USE_KIND" = true ]; then
    echo -e "${GREEN}Loading images into Kind cluster...${NC}"
    kind load docker-image ecole-platform-backend:local --name "$CLUSTER_NAME"
    kind load docker-image ecole-platform-web:local --name "$CLUSTER_NAME"
else
    echo -e "${YELLOW}Note: Images are available locally but may not be accessible to Docker Desktop Kubernetes${NC}"
fi

# Kind connectivity warning: host.docker.internal does not resolve inside Kind pods
if [ "$USE_KIND" = true ]; then
    if [[ "${DATABASE_URL:-}" == *"host.docker.internal"* ]] || [ -z "${DATABASE_URL:-}" ]; then
        echo -e "${YELLOW}WARNING: Kind pods cannot reach host.docker.internal.${NC}"
        echo -e "${YELLOW}Set DATABASE_URL and REDIS_URL to services reachable from inside the cluster.${NC}"
        echo -e "${YELLOW}Options:${NC}"
        echo "  1. Deploy Postgres + Redis in-cluster (e.g. helm install postgres bitnami/postgresql)"
        echo "  2. Use the docker-compose dev stack and pass the bridge gateway IP:"
        echo "     GATEWAY_IP=\$(docker network inspect bridge | jq -r '.[0].IPAM.Config[0].Gateway')"
        echo "     export DATABASE_URL=\"postgresql://ecole:ecole@\${GATEWAY_IP}:5432/ecole_platform\""
        echo "     export REDIS_URL=\"redis://\${GATEWAY_IP}:6379/0\""
        echo "     Then re-run this script."
        echo ""
    fi
fi

# Set namespace
NAMESPACE="ecole-local"
echo -e "${GREEN}Using namespace: $NAMESPACE${NC}"

# Create namespace
echo -e "${GREEN}Creating namespace: $NAMESPACE${NC}"
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Fail fast if using Kind with unreachable host.docker.internal
if [ "$USE_KIND" = true ]; then
    if echo "${DATABASE_URL}${REDIS_URL}" | grep -q "host.docker.internal"; then
        echo -e "${RED}Error: DATABASE_URL or REDIS_URL contains 'host.docker.internal' which is unreachable from Kind.${NC}"
        echo -e "${RED}Use the Docker bridge IP (e.g., 172.17.0.1) or a public IP instead.${NC}"
        exit 1
    fi
fi

# Create secrets from environment variables
echo -e "${GREEN}Creating secrets...${NC}"
kubectl create secret generic ecole-database-url \
    -n "$NAMESPACE" \
    --from-literal=DATABASE_URL="${DATABASE_URL:-postgresql://ecole:ecole@host.docker.internal:5432/ecole_platform}" \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic ecole-redis-url \
    -n "$NAMESPACE" \
    --from-literal=REDIS_URL="${REDIS_URL:-redis://host.docker.internal:6379/0}" \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic ecole-jwt-secret \
    -n "$NAMESPACE" \
    --from-literal=JWT_SECRET_KEY="${JWT_SECRET_KEY:-local-dev-secret-key-change-in-production}" \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic ecole-smtp-password \
    -n "$NAMESPACE" \
    --from-literal=SMTP_PASSWORD="${SMTP_PASSWORD:-}" \
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy with Helm
echo -e "${GREEN}Deploying with Helm...${NC}"
helm upgrade --install ecole-platform ./infra/k8s \
    -n "$NAMESPACE" \
    -f ./infra/k8s/values-local.yaml \
    --set images.backend.repository=ecole-platform-backend \
    --set images.backend.tag=local \
    --set images.web.repository=ecole-platform-web \
    --set images.web.tag=local \
    --wait \
    --timeout 5m

# Verify deployment
echo -e "${GREEN}Verifying deployment...${NC}"
kubectl rollout status deployment/ecole-platform-backend -n "$NAMESPACE" --timeout=120s
kubectl rollout status deployment/ecole-platform-web -n "$NAMESPACE" --timeout=60s

# Get pods
echo -e "${GREEN}Pods in $NAMESPACE namespace:${NC}"
kubectl get pods -n "$NAMESPACE"

# Print access information
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo -e "${YELLOW}Access the application via port-forwarding:${NC}"
echo ""
echo "Backend:"
echo "  kubectl port-forward -n $NAMESPACE svc/ecole-platform-backend 8000:8000"
echo "  http://localhost:8000/api/v1/health"
echo ""
echo "Web:"
echo "  kubectl port-forward -n $NAMESPACE svc/ecole-platform-web 3000:80"
echo "  http://localhost:3000"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo "  kubectl logs -n $NAMESPACE -l app.kubernetes.io/component=backend -f"
echo "  kubectl logs -n $NAMESPACE -l app.kubernetes.io/component=web -f"
echo ""
echo -e "${YELLOW}To undeploy:${NC}"
echo "  helm uninstall ecole-platform -n $NAMESPACE"
echo "  kubectl delete namespace $NAMESPACE"
