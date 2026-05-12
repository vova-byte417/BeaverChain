# 安装指南

> 本文档详细介绍 BeaverChain 的各种安装方式，从快速体验到生产环境部署。

---

## 📋 目录

- [环境要求](#环境要求)
- [Docker Compose 一键部署（推荐）](#docker-compose-一键部署推荐)
- [本地开发环境搭建](#本地开发环境搭建)
- [Kubernetes 部署](#kubernetes-部署)
- [生产环境配置](#生产环境配置)
- [常见问题](#常见问题)

---

## 环境要求

### 最低配置

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4 核 | 8 核 |
| 内存 | 8 GB | 16 GB |
| 磁盘 | 50 GB | 200 GB SSD |
| 操作系统 | Linux / macOS / Windows | Linux (Ubuntu 22.04 LTS) |

### 软件依赖

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Docker | ≥ 24.0 | 容器运行时 |
| Docker Compose | ≥ 2.0 | 容器编排 |
| Python | ≥ 3.10 | 后端运行时 |
| Node.js | ≥ 18 | 前端构建 |
| PostgreSQL | ≥ 15 | 关系型数据库 |
| Redis | ≥ 7.0 | 缓存和消息队列 |

---

## Docker Compose 一键部署（推荐）

这是最简单的安装方式，适合快速体验和小型部署。

### 1. 准备工作

```bash
# 检查 Docker 版本
docker --version
docker compose version

# 如果没有安装 Docker，请先安装
# Ubuntu/Debian:
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# macOS: 使用 Docker Desktop
# Windows: 使用 Docker Desktop for Windows
```

### 2. 克隆仓库

```bash
git clone https://github.com/vova-byte417/BeaverChain.git
cd BeaverChain
```

### 3. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env
```

关键配置项说明：

```env
# 基础配置
ENVIRONMENT=production                  # 环境类型: development/production
SECRET_KEY=your-super-secret-key-here   # 加密密钥，请修改为随机字符串

# 数据库配置
DB_HOST=postgres
DB_PORT=5432
DB_NAME=beaverchain
DB_USER=postgres
DB_PASSWORD=your-db-password

# Redis 配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# 对象存储 (MinIO/S3)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# 向量数据库
MILVUS_HOST=milvus
MILVUS_PORT=19530

# AI 提供商配置
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# 监控配置
GRAFANA_ADMIN_PASSWORD=admin123
```

### 4. 启动服务

```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
```

### 5. 验证安装

```bash
# 检查所有容器是否健康运行
docker compose ps

# 访问 Web 控制台
open http://localhost:3000

# 检查 API 是否可用
curl http://localhost:8000/health

# 预期输出: {"status": "ok", "version": "1.0.0"}
```

### 6. 默认登录

- **用户名**: `admin@beaverchain.ai`
- **密码**: `admin123`

⚠️ **重要**: 首次登录后请立即修改默认密码！

---

## 本地开发环境搭建

适合开发者进行代码调试和功能开发。

### 1. 克隆代码

```bash
git clone https://github.com/vova-byte417/BeaverChain.git
cd BeaverChain
```

### 2. 数据库服务（使用 Docker）

```bash
# 启动数据库和中间件服务
docker compose -f docker-compose.dev.yml up -d postgres redis minio milvus

# 验证服务
docker compose ps
```

### 3. 后端服务设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 复制配置
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等

# 初始化数据库
python manage.py migrate
python manage.py createsuperuser

# 创建初始数据
python manage.py seed

# 启动开发服务器
python manage.py runserver
```

后端服务将在 `http://localhost:8000` 启动。

API 文档:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 4. 前端服务设置

```bash
cd frontend

# 安装依赖
npm install

# 复制环境变量配置
cp .env.example .env

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:5173` 启动。

### 5. 验证开发环境

```bash
# 1. 访问前端
open http://localhost:5173

# 2. 检查后端健康状态
curl http://localhost:8000/health

# 3. 运行后端测试
cd backend && pytest

# 4. 运行前端测试
cd frontend && npm run test
```

---

## Kubernetes 部署

适合大规模生产环境部署。

### 1. 准备 Kubernetes 集群

你可以使用以下任一方式：

- **本地开发**: minikube / kind / k3d
- **云服务**: AWS EKS / GCP GKE / Azure AKS
- **自建**: kubeadm / k0s

```bash
# 检查集群访问
kubectl cluster-info
kubectl get nodes
```

### 2. 安装 Helm

```bash
# macOS
brew install helm

# Linux
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 验证安装
helm version
```

### 3. 部署 BeaverChain

```bash
# 添加 Helm 仓库
helm repo add beaverchain https://charts.beaverchain.ai
helm repo update

# 创建命名空间
kubectl create namespace beaverchain

# 安装（最小配置）
helm install beaverchain beaverchain/beaverchain \
  --namespace beaverchain \
  --set secrets.secretKey=$(openssl rand -hex 32)

# 查看安装状态
helm status beaverchain -n beaverchain
kubectl get pods -n beaverchain
```

### 4. 自定义配置

```bash
# 创建自定义 values 文件
cat > custom-values.yaml << EOF
# 副本数
replicaCount:
  backend: 3
  frontend: 2
  worker: 4

# 资源限制
resources:
  backend:
    requests:
      cpu: "1"
      memory: "2Gi"
    limits:
      cpu: "2"
      memory: "4Gi"

# 数据库配置
postgresql:
  enabled: true
  auth:
    password: "your-secure-password"

# Ingress 配置
ingress:
  enabled: true
  hosts:
    - host: beaverchain.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: beaverchain-tls
      hosts:
        - beaverchain.yourdomain.com
EOF

# 使用自定义配置安装
helm upgrade --install beaverchain beaverchain/beaverchain \
  --namespace beaverchain \
  -f custom-values.yaml
```

### 5. 验证部署

```bash
# 获取 Ingress 地址
kubectl get ingress -n beaverchain

# 检查所有 Pod 状态
kubectl get pods -n beaverchain -w

# 查看服务
kubectl get svc -n beaverchain

# 访问应用
open http://beaverchain.yourdomain.com
```

---

## 生产环境配置

### 1. 安全配置

```bash
# 生成强密钥
SECRET_KEY=$(openssl rand -hex 64)
DB_PASSWORD=$(openssl rand -hex 16)
REDIS_PASSWORD=$(openssl rand -hex 16)

# 更新配置文件
sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=$DB_PASSWORD/" .env
sed -i "s/^REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env
```

### 2. HTTPS 配置

使用 Let's Encrypt 免费证书：

```bash
# 安装 cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# 创建 ClusterIssuer
cat > cluster-issuer.yaml << EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
EOF

kubectl apply -f cluster-issuer.yaml
```

### 3. 数据库备份

```bash
# 配置自动备份
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup"

# 备份 PostgreSQL
docker compose exec -T postgres pg_dump -U postgres beaverchain > $BACKUP_DIR/beaverchain_$DATE.sql

# 上传到对象存储
aws s3 cp $BACKUP_DIR/beaverchain_$DATE.sql s3://your-bucket/backups/

# 保留最近 7 天备份
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
EOF

chmod +x backup.sh

# 添加到 crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/backup.sh") | crontab -
```

### 4. 监控与告警

```bash
# 访问 Grafana
kubectl port-forward svc/beaverchain-grafana 3000:80 -n monitoring

# 默认登录
# 用户: admin
# 密码: prom-operator

# 导入 BeaverChain 仪表盘
# Grafana Dashboard ID: 12345
```

### 5. 性能优化

```bash
# 数据库优化配置
# postgresql.conf 关键参数:
shared_buffers = 25% of RAM
effective_cache_size = 50-75% of RAM
work_mem = 64MB
maintenance_work_mem = 2GB

# Redis 优化
# redis.conf:
maxmemory-policy allkeys-lru
maxmemory 4gb

# 应用性能调优
# 增加工作进程数
WORKERS=8
# 调整请求超时
TIMEOUT=120
```

---

## 常见问题

### Q: 启动后数据库连接失败怎么办？

**A:** 检查以下几点：

```bash
# 1. 检查 PostgreSQL 容器状态
docker compose ps postgres
docker compose logs postgres

# 2. 测试数据库连接
docker compose exec postgres psql -U postgres -d beaverchain -c "SELECT 1;"

# 3. 检查环境变量配置
grep DB_ .env

# 4. 重启数据库服务
docker compose restart postgres
```

### Q: 前端页面加载缓慢？

**A:** 可能是以下原因：

```bash
# 1. 检查前端容器资源限制
docker stats beaverchain-frontend

# 2. 检查 API 响应时间
curl -w "%{time_total}\n" http://localhost:8000/health

# 3. 启用前端缓存
# 修改 nginx 配置，启用静态资源缓存
# 启用 gzip 压缩
```

### Q: 如何升级版本？

**A:** 使用以下步骤升级：

```bash
# 1. 备份数据库
docker compose exec postgres pg_dump -U postgres beaverchain > backup_before_upgrade.sql

# 2. 拉取最新镜像
docker compose pull

# 3. 停止旧服务
docker compose down

# 4. 启动新服务
docker compose up -d

# 5. 执行数据库迁移
docker compose exec backend python manage.py migrate

# 6. 验证升级
docker compose ps
curl http://localhost:8000/health
```

### Q: 忘记管理员密码怎么办？

**A:** 可以通过命令行重置：

```bash
# Docker 部署
docker compose exec backend python manage.py changepassword admin

# 本地部署
cd backend
python manage.py changepassword admin
```

### Q: 如何启用 SSO 单点登录？

**A:** 参考以下配置：

```env
# OAuth2 配置
OAUTH2_ENABLED=true
OAUTH2_PROVIDER=github
OAUTH2_CLIENT_ID=your-client-id
OAUTH2_CLIENT_SECRET=your-client-secret
OAUTH2_CALLBACK_URL=https://beaverchain.yourdomain.com/auth/callback

# SAML 配置
SAML_ENABLED=true
SAML_IDP_METADATA_URL=https://your-idp.com/metadata
SAML_SP_ENTITY_ID=beaverchain
```

---

## 下一步

安装完成后，建议阅读以下文档：

- 📖 [快速入门教程](quickstart.md) - 5 分钟上手核心功能
- 📖 [用户手册](user-guide.md) - 完整功能使用说明
- 📖 [API 文档](api/README.md) - 开发者 API 参考
- 📖 [部署文档](deployment.md) - 高级部署配置

---

**如有问题，请查看 [FAQ](faq.md) 或提交 GitHub Issue。**

---

*最后更新: 2026-05-12*
*文档版本: v1.0*
