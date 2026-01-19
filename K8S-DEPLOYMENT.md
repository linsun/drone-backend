# Deploying Tello Frontend and Backend to Kubernetes

## Prerequisites

1. A Kubernetes cluster
2. `kubectl` configured to access your cluster
3. Docker installed to build images
4. Access to a container registry (Docker Hub, GCR, ECR, etc.)

## Important Considerations

### Network Requirements

The **Tello drone requires a direct WiFi connection** to communicate with the backend. The backend pod needs to reach the Tello at `192.168.10.1:8889`.

**Options:**

1. **hostNetwork Mode** (Simplest):
   - Uncomment `hostNetwork: true` in `k8s-backend-deployment.yaml`
   - The backend pod will use the host's network stack
   - The Kubernetes node must be connected to Tello WiFi

2. **Dedicated Node** (Recommended):
   - Label a specific node that can connect to Tello WiFi:
     ```bash
     kubectl label nodes <node-name> tello-network=true
     ```
   - Uncomment the `nodeSelector` section in `k8s-backend-deployment.yaml`
   - Ensure that node is connected to the Tello WiFi network

3. **Single-Node Cluster** (Easiest):
   - If running a single-node cluster (minikube, k3s, etc.), just connect that node to Tello WiFi
   - No special configuration needed

## Step 1: Build Docker Images

### Backend

```bash
cd /path/to/tello-backend

# Build the image
docker build -f ../outputs/Dockerfile.backend -t tello-backend:latest .

# Tag for your registry (if pushing to remote registry)
docker tag tello-backend:latest your-registry/tello-backend:latest

# Push to registry (optional, skip for local clusters)
docker push your-registry/tello-backend:latest
```

### Frontend

```bash
cd /path/to/tello-frontend

# Build the image
docker build -f ../outputs/Dockerfile.frontend -t tello-frontend:latest .

# Tag for your registry (if pushing to remote registry)
docker tag tello-frontend:latest your-registry/tello-frontend:latest

# Push to registry (optional, skip for local clusters)
docker push your-registry/tello-frontend:latest
```

**For local clusters (minikube, k3s, Docker Desktop):**
- You can skip pushing to a registry
- Make sure to set `imagePullPolicy: IfNotPresent` or `Never`

**For minikube specifically:**
```bash
# Load images directly into minikube
minikube image load tello-backend:latest
minikube image load tello-frontend:latest
```

## Step 2: Update Image References

If using a remote registry, update the image names in:
- `k8s-backend-deployment.yaml`: Change `image: tello-backend:latest`
- `k8s-frontend-deployment.yaml`: Change `image: tello-frontend:latest`

To your registry paths, e.g., `your-registry/tello-backend:latest`

## Step 3: Deploy to Kubernetes

```bash
# Deploy backend
kubectl apply -f k8s-backend-deployment.yaml

# Deploy frontend
kubectl apply -f k8s-frontend-deployment.yaml

# (Optional) Deploy ingress
kubectl apply -f k8s-ingress.yaml
```

## Step 4: Verify Deployment

```bash
# Check pods are running
kubectl get pods

# Check services
kubectl get services

# View backend logs
kubectl logs -f deployment/tello-backend

# View frontend logs
kubectl logs -f deployment/tello-frontend
```

## Step 5: Access the Application

### Option A: Using LoadBalancer (if available)

```bash
# Get the external IP
kubectl get service tello-frontend

# Access at http://<EXTERNAL-IP>
```

### Option B: Using NodePort

```bash
# Change service type to NodePort in k8s-frontend-deployment.yaml
# Then get the node port
kubectl get service tello-frontend

# Access at http://<NODE-IP>:<NODE-PORT>
```

### Option C: Using Port Forward (for testing)

```bash
# Forward frontend port
kubectl port-forward service/tello-frontend 3000:80

# Forward backend port (if needed)
kubectl port-forward service/tello-backend 3001:3001

# Access at http://localhost:3000
```

### Option D: Using Ingress (recommended for production)

1. Install an ingress controller (if not already installed):
   ```bash
   # Example: NGINX Ingress Controller
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
   ```

2. Update `k8s-ingress.yaml` with your domain

3. Apply the ingress:
   ```bash
   kubectl apply -f k8s-ingress.yaml
   ```

4. Access at `http://tello.example.com`

## Configuration

### Environment Variables

You can add environment variables to the backend deployment:

```yaml
env:
- name: TELLO_IP
  value: "192.168.10.1"
- name: LOG_LEVEL
  value: "INFO"
```

### Persistent Storage for Photos/Videos

To persist photos and videos, replace `emptyDir` with a `PersistentVolumeClaim`:

```yaml
volumes:
- name: photos
  persistentVolumeClaim:
    claimName: tello-photos-pvc
- name: videos
  persistentVolumeClaim:
    claimName: tello-videos-pvc
```

Create PVCs:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: tello-photos-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

## Troubleshooting

### Backend can't connect to Tello

1. **Check network connectivity:**
   ```bash
   # Exec into backend pod
   kubectl exec -it deployment/tello-backend -- /bin/bash

   # Try to ping Tello
   ping 192.168.10.1
   ```

2. **Enable hostNetwork:**
   - Uncomment `hostNetwork: true` in backend deployment
   - Redeploy: `kubectl rollout restart deployment/tello-backend`

3. **Verify node has Tello WiFi:**
   - SSH into the node
   - Check WiFi connection: `ifconfig` or `ip addr`
   - Verify you can reach `192.168.10.1`

### Frontend can't reach backend

1. **Check service endpoint:**
   ```bash
   kubectl get endpoints tello-backend
   ```

2. **Test from frontend pod:**
   ```bash
   kubectl exec -it deployment/tello-frontend -- /bin/sh
   wget -O- http://tello-backend:3001/api/status
   ```

3. **Update frontend config:**
   - The frontend needs to point to the correct backend URL
   - In production, this is typically done via environment variables at build time

### Video streaming issues

1. **Increase timeouts in Ingress:**
   ```yaml
   nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
   nginx.ingress.kubernetes.io/proxy-send-timeout: "600"
   ```

2. **Check resource limits:**
   - Video streaming is CPU/memory intensive
   - Increase limits in deployment if needed

## Production Considerations

1. **Use proper secrets management** for any sensitive data
2. **Set up monitoring** (Prometheus/Grafana)
3. **Configure autoscaling** for frontend (backend should stay at 1 replica)
4. **Use TLS/HTTPS** with cert-manager
5. **Set resource requests/limits** appropriately
6. **Configure health checks** properly
7. **Use a proper storage solution** for photos/videos (S3, NFS, etc.)

## Clean Up

```bash
# Delete all resources
kubectl delete -f k8s-backend-deployment.yaml
kubectl delete -f k8s-frontend-deployment.yaml
kubectl delete -f k8s-ingress.yaml
```

## Next Steps

- Set up CI/CD pipeline to automate builds and deployments
- Configure monitoring and alerting
- Implement proper backup strategy for photos/videos
- Add authentication if exposing publicly
