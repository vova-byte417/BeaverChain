# 部署指南

本文档详细介绍 BeaverChain 平台的各种部署方式，从开发环境到生产环境的完整配置。

## 📋 目录

- [部署架构](#部署架构)
- [环境要求](#环境要求)
- [开发环境部署](#开发环境部署)
- [Docker Compose 部署](#docker-compose-部署)
- [Kubernetes 部署](#kubernetes-部署)
- [生产环境最佳实践](#生产环境最佳实践)
- [高可用配置](#高可用配置)
- [监控与告警](#监控与告警)

## 部署架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                           负载均衡                                │
│                          (Nginx/ALB)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Frontend    │    │   Frontend    │    │   Frontend    │
│  (React/Vite) │    │  (React/Vite) │    │  (React/Vite) │
└───────────────┘    └───────────────┘    └───────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   API Server  │    │   API Server  │    │   API Server  │
│  (FastAPI)    │    │  (FastAPI)    │    │  (FastAPI)    │
└───────────────┘    └───────────────┘    └───────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   PostgreSQL  │    │    Redis      │    │  S3 Storage   │
│  (Primary)    │    │  (Cluster)    │    │  (MinIO/AWS)  │
└───────────────┘    └───────────────┘    └───────────────┘
        │
        ▼
┌───────────────┐
│  PostgreSQL   │
│  (Replica)    │
└───────────────┘
```

### 组件说明

| 组件 | 用途 | 高可用模式 |
|------|------|-----------|
| Frontend | 用户交互界面 | 多副本 + CDN |
| API Server | REST API 服务 | 多副本 + 负载均衡 |
| PostgreSQL | 主数据库 | 主从复制 |
| Redis | 缓存、任务队列 | 哨兵集群 |
| S3 Storage | 模型存储 | 分布式存储 |
| GPU Nodes | 模型推理节点 | 弹性伸缩组 |

## 环境要求

### 硬件要求

#### 开发环境（最低配置）

| 资源 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 4 核 | 8 核 |
| 内存 | 8 GB | 16 GB |
| 存储 | 100 GB SSD | 500 GB NVMe SSD |
| GPU | 可选 | NVIDIA RTX 3090/4090 |

#### 生产环境（推荐配置）

| 节点类型 | CPU | 内存 | GPU | 存储 | 数量 |
|---------|-----|------|-----|------|------|
| API 节点 | 16 核 | 32 GB | - | 500 GB NVMe | 3+ |
| 数据库节点 | 8 核 | 64 GB | - | 2 TB NVMe | 3+ |
| 推理节点 | 32 核 | 128 GB | A100 80GB x8 | 4 TB NVMe | 2+ |
| 监控节点 | 8 核 | 16 GB | - | 500 GB SSD | 1+ |

### 软件要求

| 软件 | 版本要求 |
|------|---------|
| 操作系统 | Ubuntu 22.04 LTS / CentOS 8+ |
| Docker | ≥ 24.0 |
| Docker Compose | ≥ 2.0 |
| Kubernetes | ≥ 1.26 |
| NVIDIA Driver | ≥ 525.60 |
| CUDA | ≥ 12.0 |

## 开发环境部署

### 一键启动脚本

```bash
# 克隆项目
git clone https://github.com/vova-byte417/BeaverChain.git
cd BeaverChain

# 启动开发环境
./scripts/dev/start.sh
```

### 手动启动步骤

#### 1. 启动依赖服务

```bash
# 启动 PostgreSQL
docker run -d \
  --name beaverchain-postgres \
  -e POSTGRES_DB=beaverchain \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  postgres:15-alpine

# 启动 Redis
docker run -d \
  --name beaverchain-redis \
  -p 6379:6379 \
  redis:7-alpine

# 启动 MinIO（S3 兼容存储）
docker run -d \
  --name beaverchain-minio \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=secure_password \
  -p 9000:9000 \
  -p 9001:9001 \
  minio/minio:latest server /data --console-address ":9001"
```

#### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://admin:secure_password@localhost:5432/beaverchain

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# S3 存储配置
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=admin
S3_SECRET_KEY=secure_password
S3_BUCKET=beaverchain-models

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# JWT 配置
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
```

#### 3. 初始化数据库

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 创建初始管理员用户
python -m scripts.create_admin --email admin@beaverchain.com --password admin123
```

#### 4. 启动后端服务

```bash
# 启动 API 服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动任务 Worker（新终端）
celery -A worker.app worker --loglevel=info --concurrency=4
```

#### 5. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

#### 6. 验证部署

```bash
# 检查 API 健康状态
curl http://localhost:8000/health

# 预期输出:
# {"status":"healthy","version":"1.0.0","timestamp":1715000000}

# 访问前端界面
open http://localhost:5173
```

## Docker Compose 部署

### 基础部署

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### docker-compose.yml 配置详解

```yaml
version: '3.8'

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: beaverchain
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD:-secure_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin -d beaverchain"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 缓存
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MinIO 对象存储
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-admin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-secure_password}
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # API 服务
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://admin:${DB_PASSWORD:-secure_password}@postgres:5432/beaverchain
      REDIS_URL: redis://redis:6379/0
      S3_ENDPOINT: http://minio:9000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s

  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - api
    deploy:
      replicas: 2

  # 任务 Worker
  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A worker.app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://admin:${DB_PASSWORD:-secure_password}@postgres:5432/beaverchain
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      replicas: 4

  # GPU 推理节点（可选）
  inference-gpu:
    build:
      context: .
      dockerfile: Dockerfile.gpu
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    runtime: nvidia
    environment:
      NVIDIA_VISIBLE_DEVICES: all

  # Prometheus 监控
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  # Grafana 仪表盘
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  postgres_data:
  redis_data:
  minio_data:
  prometheus_data:
  grafana_data:
```

### 扩展部署配置

#### 启用 HTTPS

1. 配置 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. 使用 Let's Encrypt 获取证书：

```bash
certbot --nginx -d your-domain.com
```

## Kubernetes 部署

### 前置准备

```bash
# 安装 kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# 安装 Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 验证集群连接
kubectl cluster-info
```

### Helm Chart 部署

```bash
# 添加 Helm 仓库
helm repo add beaverchain https://charts.beaverchain.com
helm repo update

# 安装 Chart
helm install beaverchain beaverchain/beaverchain \
  --namespace beaverchain \
  --create-namespace \
  --values custom-values.yaml
```

### 自定义配置 custom-values.yaml

```yaml
# 全局配置
global:
  imagePullSecrets:
    - name: regcred
  storageClass: gp3
  domain: beaverchain.yourcompany.com

# API 服务配置
api:
  replicaCount: 3
  image:
    repository: beaverchain/api
    tag: v1.0.0
  resources:
    requests:
      cpu: "2"
      memory: "4Gi"
    limits:
      cpu: "4"
      memory: "8Gi"
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

# 前端配置
frontend:
  replicaCount: 2
  image:
    repository: beaverchain/frontend
    tag: v1.0.0
  ingress:
    enabled: true
    annotations:
      kubernetes.io/ingress.class: nginx
      cert-manager.io/cluster-issuer: letsencrypt-prod
    hosts:
      - host: beaverchain.yourcompany.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: beaverchain-tls
        hosts:
          - beaverchain.yourcompany.com

# PostgreSQL
postgresql:
  enabled: true
  architecture: replication
  auth:
    database: beaverchain
    username: admin
    password: secure_password
  primary:
    persistence:
      size: 500Gi
  readReplicas:
    replicaCount: 2

# Redis
redis:
  enabled: true
  architecture: replication
  auth:
    password: secure_password
  master:
    persistence:
      size: 100Gi
  replica:
    replicaCount: 2

# GPU 推理节点
inference:
  enabled: true
  gpuCount: 8
  gpuType: nvidia.com/A100-SXM4-80GB
  replicaCount: 2
  autoscaling:
    enabled: true
    minReplicas: 1
    maxReplicas: 10
    metrics:
      - type: GPU
        averageUtilization: 70

# 监控
monitoring:
  enabled: true
  prometheus:
    retention: 30d
    storage: 500Gi
  grafana:
    enabled: true
    adminPassword: secure_password
  alertmanager:
    enabled: true
    config:
      receivers:
        - name: slack
          slack_configs:
            - api_url: https://hooks.slack.com/services/XXX
              channel: '#alerts'
```

### GPU 节点配置

确保 Kubernetes 集群有 GPU 节点可用：

```bash
# 检查 GPU 节点
kubectl get nodes "-o=custom-columns=NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu"

# 给 GPU 节点打标签
kubectl label nodes gpu-node-1 accelerator=nvidia-gpu
kubectl label nodes gpu-node-1 gpu-type=a100

# 安装 NVIDIA GPU Operator
helm install --wait --generate-name \
  -n gpu-operator --create-namespace \
  nvidia/gpu-operator
```

## 生产环境最佳实践

### 安全配置

#### 1. 网络安全

```yaml
# 网络策略示例
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: beaverchain-network-policy
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - ipBlock:
            cidr: 10.0.0.0/16
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 169.254.169.254/32  # 阻止访问云元数据服务
```

#### 2. Secrets 管理

使用 Kubernetes Secrets 或 HashiCorp Vault：

```bash
# 创建数据库密码 Secret
kubectl create secret generic beaverchain-db-secret \
  --from-literal=username=admin \
  --from-literal=password=secure_password

# 创建 API Key Secret
kubectl create secret generic beaverchain-api-secret \
  --from-literal=jwt-secret=your-super-secret-key
```

#### 3. RBAC 配置

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: beaverchain-reader
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
```

### 性能优化

#### 1. 数据库优化

```sql
-- PostgreSQL 配置优化
ALTER SYSTEM SET shared_buffers = '16GB';
ALTER SYSTEM SET effective_cache_size = '48GB';
ALTER SYSTEM SET maintenance_work_mem = '2GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 500;
```

#### 2. Redis 优化

```conf
# redis.conf
maxmemory 32gb
maxmemory-policy allkeys-lfu
appendonly yes
appendfsync everysec
aof-use-rdb-preamble yes
```

#### 3. GPU 推理优化

```python
# vLLM 优化配置
vllm_config = {
    "tensor_parallel_size": 8,
    "max_num_batched_tokens": 8192,
    "max_num_seqs": 256,
    "gpu_memory_utilization": 0.95,
    "enforce_eager": True,
    "quantization": "awq"
}
```

### 备份策略

#### 1. 数据库备份

```bash
# 每日全量备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="/backup/beaverchain-$DATE.sql.gz"

pg_dump -h localhost -U admin beaverchain | gzip > $BACKUP_FILE

# 上传到 S3
aws s3 cp $BACKUP_FILE s3://beaverchain-backups/database/

# 保留 30 天
find /backup -name "*.sql.gz" -mtime +30 -delete
```

#### 2. 模型备份

```bash
# 模型版本快照
aws s3 sync /models s3://beaverchain-models-snapshot/$(date +%Y%m%d)/ \
  --delete
```

## 高可用配置

### 多可用区部署

```yaml
# Pod 反亲和性配置
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - beaverchain-api
        topologyKey: topology.kubernetes.io/zone
```

### 故障转移配置

```yaml
# 就绪探针和存活探针
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  successThreshold: 1
  failureThreshold: 3

livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 5
```

## 监控与告警

### Prometheus 指标配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts.yml"

scrape_configs:
  - job_name: 'beaverchain-api'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: beaverchain-api
        action: keep
      - source_labels: [__meta_kubernetes_pod_container_port_number]
        regex: "8000"
        action: keep

  - job_name: 'beaverchain-inference'
    static_configs:
      - targets: ['inference-service:8080/metrics']
```

### 告警规则示例

```yaml
# alerts.yml
groups:
  - name: beaverchain_alerts
    rules:
      - alert: HighAPIErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "高 API 错误率"
          description: "API 错误率超过 5%，当前值: {{ $value }}"

      - alert: HighGPUUtilization
        expr: avg(gpu_utilization) by (instance) > 90
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "GPU 使用率过高"
          description: "实例 {{ $labels.instance }} GPU 使用率超过 90%"

      - alert: DatabaseConnectionPoolExhausted
        expr: pg_stat_database_numbackends > 80
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "数据库连接池耗尽"
```

### Grafana 仪表盘

部署后访问 Grafana 查看预配置的仪表盘：

- **系统概览仪表盘** - 整体健康状态、QPS、延迟
- **API 性能仪表盘** - 端点性能、错误率、响应时间
- **GPU 监控仪表盘** - GPU 使用率、显存、温度
- **数据库仪表盘** - 连接数、查询延迟、锁等待
- **业务指标仪表盘** - 模型调用量、Token 消耗、成本统计

---

## 📞 部署支持

如遇部署问题：

1. 查看 [故障排查指南](./TROUBLESHOOTING.md)
2. 检查系统日志 `journalctl -u beaverchain`
3. 查看应用日志 `kubectl logs -l app=beaverchain-api`
4. 在 GitHub 提交 Issue 并附上日志

**文档版本**: v1.0.0  
**最后更新**: 2024-05-13
