# FlowInbox AI — Local Kubernetes (kind) & CI/CD Guide

This directory contains the Kubernetes manifests for running **FlowInbox AI** on a local [`kind`](https://kind.sigs.k8s.io/) cluster.

---

## 🛠️ Step-by-Step Local Deployment Guide

### 1. Create Local kind Cluster
If you haven't already created the cluster, run:
```bash
kind create cluster --name flowinbox
```
*(Optional with Ingress support)*:
```bash
kind create cluster --name flowinbox --config - <<EOF
apiVersion: kind.x-k8s.io/v1alpha4
kind: Cluster
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    apiVersion: kubeadm.k8s.io/v1beta3
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
EOF
```

To enable Ingress on kind:
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

---

### 2. Build Docker Images Locally
From the root of the repository, build the backend and frontend Docker images:
```bash
docker build -t flowinbox-backend:local ./flowinbox/backend
docker build -t flowinbox-frontend:local ./flowinbox/frontend
```

---

### 3. Load Images into the kind Cluster
`kind` uses an isolated `containerd` runtime inside its node container and cannot automatically access images stored only in the host Docker daemon image store. Load them directly:
```bash
kind load docker-image flowinbox-backend:local --name flowinbox
kind load docker-image flowinbox-frontend:local --name flowinbox
```

---

### 4. Configure Application Secrets
Copy the secret template to create your local `secret.yaml`:
```bash
cp k8s/secret.yaml.example k8s/secret.yaml
```
Open `k8s/secret.yaml` and replace placeholders (`GROQ_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `JWT_SECRET`) with your actual keys from `flowinbox/backend/.env`.

*(Note: `k8s/secret.yaml` is listed in `.gitignore` and must never be committed).*

---

### 5. Apply Kubernetes Manifests
Apply the resources in dependency order:
```bash
# 1. Create Namespace
kubectl apply -f k8s/namespace.yaml

# 2. Apply ConfigMap and Secret
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 3. Apply Storage, Deployments, Services, and Ingress
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml

kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

kubectl apply -f k8s/qdrant-pvc.yaml
kubectl apply -f k8s/qdrant-deployment.yaml
kubectl apply -f k8s/qdrant-service.yaml

kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml

kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml

kubectl apply -f k8s/ingress.yaml
```

Alternatively, apply the entire folder:
```bash
kubectl apply -f k8s/
```

---

## 🔍 Verification & Operation Commands

### Check Pod Health
```bash
kubectl get pods -n flowinbox
```
**Expected Healthy Output:**
```text
NAME                        READY   STATUS    RESTARTS   AGE
backend-56f87498c4-abc12    1/1     Running   0          45s
frontend-6b4594c798-def34   1/1     Running   0          45s
postgres-786d5c645b-ghi56   1/1     Running   0          45s
qdrant-67d98877bf-jkl78     1/1     Running   0          45s
redis-5494d4d68c-mno90      1/1     Running   0          45s
```

### Accessing the Application
- **Via Ingress (Port 80)**: Open `http://localhost` in your browser.
- **Via Direct Port-Forwarding**:
  ```bash
  # Forward Frontend (accessible at http://localhost:8080 or http://localhost:3000)
  kubectl port-forward -n flowinbox svc/frontend 8080:80

  # Forward Backend API
  kubectl port-forward -n flowinbox svc/backend 8000:8000
  ```

### Verify Health Endpoint
```bash
curl http://localhost:8000/api/v1/health
# Response: {"status":"healthy","database":"connected","redis":"connected","qdrant":"connected"}
```

### Tail Logs & Debug Pods
```bash
# Stream Backend Logs
kubectl logs -n flowinbox deploy/backend -f

# Exec into Backend Pod
kubectl exec -n flowinbox -it deploy/backend -- /bin/sh
```

### Test Automatic Pod Recovery
Demonstrate Kubernetes self-healing by killing a pod:
```bash
# 1. Note pod name
kubectl get pods -n flowinbox

# 2. Delete backend pod
kubectl delete pod -n flowinbox <backend-pod-name>

# 3. Confirm Kubernetes automatically spawns a replacement pod
kubectl get pods -n flowinbox
```

---

## 🔄 CI/CD Automation (GitHub Actions)

- **`ci.yml`**: Runs automatically on Pull Requests and pushes to `main`. Executes backend `pytest` suite and verifies frontend build.
- **`cd.yml`**: Runs on push to `main` after CI passes. Logins to GitHub Container Registry (GHCR), builds Docker images tagged with Git short SHA and `latest`, and pushes to `ghcr.io/<owner>/flowinbox-backend` and `ghcr.io/<owner>/flowinbox-frontend`.
