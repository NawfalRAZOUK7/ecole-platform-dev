# Kubernetes Setup Plan — Corrected

## Issues Identified

### 1. Secret Key Mismatch
**Problem**: Helm templates expect secret keys `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `SMTP_PASSWORD` but the create-local-secrets.sh script creates keys `database-url`, `redis-url`, `jwt-secret`, `smtp-password`.

**Fix**: Update create-local-secrets.sh to use correct keys.

### 2. Local Image Access
**Problem**: Docker Desktop Kubernetes runs in a VM and cannot access locally built Docker images directly. The images show `ErrImageNeverPull`.

**Fix Options**:
- Use Kind instead of Docker Desktop (recommended for local dev)
- Push images to a local registry
- Use Docker Desktop's built-in registry

### 3. Namespace Ownership
**Problem**: Manual namespace creation without Helm labels causes Helm to fail with "invalid ownership metadata".

**Fix**: Let Helm create the namespace via the namespace template, or add proper labels when creating manually.

### 4. External Service Connectivity
**Problem**: Using `host.docker.internal` for database/redis works in Docker Compose but may not work in Kubernetes pods.

**Fix**: For local Kubernetes, either:
- Deploy Postgres/Redis in the same cluster
- Use a different networking approach (host alias, NodePort, etc.)

---

## Recommended Approach: Kind for Local Development

**Why Kind over Docker Desktop Kubernetes**:
- Built-in `kind load docker-image` for local images
- Better control over cluster lifecycle
- Easier to reset and recreate
- Matches GitHub Actions E2E test setup

---

## Implementation Plan

### Phase 1: Fix Secret Keys
**File**: `infra/k8s/create-local-secrets.sh`

Change secret keys from kebab-case to UPPER_CASE:
- `database-url` → `DATABASE_URL`
- `redis-url` → `REDIS_URL`
- `jwt-secret` → `JWT_SECRET_KEY`
- `smtp-password` → `SMTP_PASSWORD`

### Phase 2: Update deploy-local.sh for Kind
**File**: `infra/k8s/deploy-local.sh`

Changes:
- Detect if using Kind
- Use `kind load docker-image` for Kind
- Use `docker load` for Docker Desktop (if needed)
- Don't create namespace manually (let Helm do it)
- Use correct secret keys

### Phase 3: Simplify values-local.yaml
**File**: `infra/k8s/values-local.yaml`

Changes:
- Disable namespace creation (let script handle it)
- Use `imagePullPolicy: Never` for Kind (images are pre-loaded)
- Keep local configuration (debug mode, no TLS, etc.)

### Phase 4: Deploy Local Services (Optional)
For complete local Kubernetes setup, deploy Postgres and Redis in the cluster:
- Add to values-local.yaml or use separate Helm charts
- Or use `host.docker.internal` with hostAliases

### Phase 5: Update Documentation
**File**: `docs/KUBERNETES_SETUP.md`

Create clear instructions for:
- Using Kind for local development
- Alternative: Docker Desktop with local registry
- Secret creation
- Deployment steps
- Troubleshooting

---

## Step-by-Step Implementation

### Step 1: Fix Secret Keys
```bash
# Update create-local-secrets.sh
# Change all --from-literal keys to UPPER_CASE
```

### Step 2: Update deploy-local.sh
```bash
# Add Kind detection
# Use kind load docker-image for Kind clusters
# Don't create namespace manually
# Use correct secret keys
```

### Step 3: Update values-local.yaml
```yaml
namespace:
  create: false  # Script will handle namespace

images:
  backend:
    pullPolicy: Never  # For Kind (images pre-loaded)
  web:
    pullPolicy: Never
```

### Step 4: Create Kind Cluster and Deploy
```bash
# Create Kind cluster
kind create cluster --name ecole-dev

# Build images
docker build -t ecole-platform-backend:local ./backend
docker build -t ecole-platform-web:local ./web

# Load images into Kind
kind load docker-image ecole-platform-backend:local --name ecole-dev
kind load docker-image ecole-platform-web:local --name ecole-dev

# Create namespace
kubectl create namespace ecole-local

# Create secrets with correct keys
./infra/k8s/create-local-secrets.sh ecole-local

# Deploy with Helm
helm upgrade --install ecole-platform ./infra/k8s \
  -n ecole-local \
  -f ./infra/k8s/values-local.yaml \
  --set images.backend.repository=ecole-platform-backend \
  --set images.backend.tag=local \
  --set images.web.repository=ecole-platform-web \
  --set images.web.tag=local \
  --wait
```

### Step 5: Access Services
```bash
# Port-forward to access
kubectl port-forward -n ecole-local svc/ecole-platform-ecole-platform-backend 8000:8000
kubectl port-forward -n ecole-local svc/ecole-platform-ecole-platform-web 3000:80
```

---

## Alternative: Docker Desktop with Local Registry

If you prefer Docker Desktop over Kind:

### Setup Local Registry
```bash
docker run -d -p 5001:5000 --restart=always --name local-registry registry:2
```

### Configure Docker Desktop
1. Docker Desktop → Settings → Docker Engine
2. Add:
```json
{
  "insecure-registries": ["localhost:5001"]
}
```
3. Apply & Restart

### Push to Local Registry
```bash
docker tag ecole-platform-backend:local localhost:5001/ecole-platform-backend:local
docker tag ecole-platform-web:local localhost:5001/ecole-platform-web:local
docker push localhost:5001/ecole-platform-backend:local
docker push localhost:5001/ecole-platform-web:local
```

### Update values-local.yaml
```yaml
images:
  backend:
    repository: localhost:5001/ecole-platform-backend
    tag: local
    pullPolicy: Always
  web:
    repository: localhost:5001/ecole-platform-web
    tag: local
    pullPolicy: Always
```

---

## Summary

**Recommended**: Use Kind for local Kubernetes development
- Easier image handling with `kind load docker-image`
- Matches GitHub Actions E2E setup
- Better control over cluster lifecycle

**Alternative**: Docker Desktop with local registry
- More complex setup
- Requires registry configuration
- Useful if you already use Docker Desktop heavily
