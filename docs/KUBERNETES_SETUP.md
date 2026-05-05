# Kubernetes Local Development Setup

This guide covers running the École Platform on a local Kubernetes cluster using **Kind** (Kubernetes in Docker). Kind is the recommended approach because it supports `kind load docker-image` for local images and matches the GitHub Actions E2E test setup.

---

## Prerequisites

```bash
brew install kubectl helm kind docker jq
```

Verify:
```bash
kubectl version --client
helm version
kind version
docker info
```

---

## Option A — Kind (Recommended)

### 1. Create a Kind cluster

```bash
kind create cluster --name ecole-dev
# Verify context was switched automatically:
kubectl config current-context  # should print: kind-ecole-dev
```

### 2. Build local images

Run from the repository root:
```bash
docker build -t ecole-platform-backend:local ./backend
docker build -t ecole-platform-web:local ./web
```

### 3. Load images into Kind

Kind runs inside Docker and cannot pull from your local daemon. Load images explicitly:
```bash
kind load docker-image ecole-platform-backend:local --name ecole-dev
kind load docker-image ecole-platform-web:local --name ecole-dev
```

### 4. Configure external service connectivity

Kind pods **cannot** reach `host.docker.internal`. You need to point `DATABASE_URL` and `REDIS_URL` at something reachable from inside the cluster.

**Option A — Start the docker-compose dev stack first, then use the bridge gateway IP:**
```bash
cd infra && docker-compose -f docker-compose.dev.yml up -d postgres redis
GATEWAY_IP=$(docker network inspect bridge | jq -r '.[0].IPAM.Config[0].Gateway')
export DATABASE_URL="postgresql://ecole:ecole@${GATEWAY_IP}:5432/ecole_platform"
export REDIS_URL="redis://${GATEWAY_IP}:6379/0"
```

**Option B — Deploy Postgres and Redis in-cluster:**
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql \
  -n ecole-local --create-namespace \
  --set auth.username=ecole --set auth.password=ecole --set auth.database=ecole_platform
helm install redis bitnami/redis \
  -n ecole-local \
  --set auth.enabled=false

export DATABASE_URL="postgresql://ecole:ecole@postgres-postgresql.ecole-local.svc.cluster.local:5432/ecole_platform"
export REDIS_URL="redis://redis-master.ecole-local.svc.cluster.local:6379/0"
```

### 5. Create namespace and secrets

```bash
kubectl create namespace ecole-local --dry-run=client -o yaml | kubectl apply -f -
./infra/k8s/create-local-secrets.sh ecole-local
```

To override secrets with custom values:
```bash
export JWT_SECRET_KEY="my-local-secret"
./infra/k8s/create-local-secrets.sh ecole-local
```

### 6. Deploy with Helm

```bash
helm upgrade --install ecole-platform ./infra/k8s \
  -n ecole-local \
  -f ./infra/k8s/values-local.yaml \
  --set images.backend.repository=ecole-platform-backend \
  --set images.backend.tag=local \
  --set images.web.repository=ecole-platform-web \
  --set images.web.tag=local \
  --wait --timeout 5m
```

Or use the convenience script (which runs steps 2–6 automatically):
```bash
./infra/k8s/deploy-local.sh
```

### 7. Access services

The ingress is disabled for local; use port-forwarding:
```bash
# Backend API
kubectl port-forward -n ecole-local svc/ecole-platform-ecole-platform-backend 8000:8000
curl http://localhost:8000/api/v1/health

# Web UI
kubectl port-forward -n ecole-local svc/ecole-platform-ecole-platform-web 3000:80
open http://localhost:3000
```

---

## Option B — Docker Desktop Kubernetes with a Local Registry

Use this if you already use Docker Desktop and do not want to install Kind.

### 1. Enable Kubernetes in Docker Desktop

Docker Desktop → Settings → Kubernetes → Enable Kubernetes → Apply & Restart.

### 2. Start a local image registry

```bash
docker run -d -p 5001:5000 --restart=always --name local-registry registry:2
```

Configure Docker Desktop to trust it: Settings → Docker Engine, add:
```json
{
  "insecure-registries": ["localhost:5001"]
}
```
Apply & Restart.

### 3. Build and push images to the local registry

```bash
docker build -t localhost:5001/ecole-platform-backend:local ./backend
docker build -t localhost:5001/ecole-platform-web:local ./web
docker push localhost:5001/ecole-platform-backend:local
docker push localhost:5001/ecole-platform-web:local
```

### 4. Deploy

`host.docker.internal` resolves correctly in Docker Desktop Kubernetes pods, so you can use the default URLs:
```bash
kubectl create namespace ecole-local --dry-run=client -o yaml | kubectl apply -f -
./infra/k8s/create-local-secrets.sh ecole-local

helm upgrade --install ecole-platform ./infra/k8s \
  -n ecole-local \
  -f ./infra/k8s/values-local.yaml \
  --set images.backend.repository=localhost:5001/ecole-platform-backend \
  --set images.backend.tag=local \
  --set images.web.repository=localhost:5001/ecole-platform-web \
  --set images.web.tag=local \
  --set images.backend.pullPolicy=Always \
  --set images.web.pullPolicy=Always \
  --wait --timeout 5m
```

---

## Verifying the Deployment

```bash
# Check all pods are Running
kubectl get pods -n ecole-local

# Watch rollout
kubectl rollout status deploy/ecole-platform-ecole-platform-backend -n ecole-local
kubectl rollout status deploy/ecole-platform-ecole-platform-web -n ecole-local

# View backend logs
kubectl logs -n ecole-local -l app.kubernetes.io/component=backend -f

# View worker logs
kubectl logs -n ecole-local -l app.kubernetes.io/component=worker -f
```

---

## Teardown

```bash
# Uninstall Helm release
helm uninstall ecole-platform -n ecole-local

# Delete namespace and all resources
kubectl delete namespace ecole-local

# Delete Kind cluster (if using Kind)
kind delete cluster --name ecole-dev
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ErrImageNeverPull` | Image not loaded into Kind | Run `kind load docker-image <image>:<tag> --name ecole-dev` |
| `ErrImagePull` | Image not in registry | Push to local registry and set `pullPolicy: Always` |
| Pod crashloops on DB connect | `host.docker.internal` not resolving in Kind | See §4 — use gateway IP or in-cluster services |
| `invalid ownership metadata` | Namespace created without Helm labels and Helm tries to manage it | Pre-create namespace via `kubectl create namespace` before `helm install`; do not set `namespace.create: true` in values |
| Migration initContainer fails | Database not ready | The initContainer retries up to 30× with 5s delay; check DB connectivity first |
| Worker pod stays `Running` but tasks stall | Redis connection lost | The liveness probe pings Redis every 60s and restarts the pod after 3 failures |
