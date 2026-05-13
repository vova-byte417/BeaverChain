# 故障排查指南

本文档提供 BeaverChain 平台常见问题的诊断方法和解决方案。请按照目录顺序排查问题。

## 📋 目录

- [快速诊断](#快速诊断)
- [安装与启动问题](#安装与启动问题)
- [数据库相关问题](#数据库相关问题)
- [模型管理问题](#模型管理问题)
- [部署与推理问题](#部署与推理问题)
- [API 接口问题](#api-接口问题)
- [Computer-Use (CUA) 问题](#computer-use-cua-问题)
- [性能问题](#性能问题)
- [安全与权限问题](#安全与权限问题)
- [日志与诊断](#日志与诊断)
- [联系支持](#联系支持)

## 快速诊断

### 运行健康检查

```bash
# 一键诊断所有组件
make health-check

# 或手动检查
curl http://localhost:8000/health
```

**健康检查响应说明:**

```json
{
  "status": "healthy",           # overall: healthy / degraded / unhealthy
  "version": "1.0.0",
  "timestamp": 1715600000,
  "components": {
    "database": "connected",     # connected / disconnected / error
    "redis": "connected",
    "model_serving": "running",  # running / stopped / error
    "gpu_available": true,
    "gpu_count": 8,
    "gpu_memory_used": "24.5GB",
    "gpu_memory_total": "640GB"
  }
}
```

### 收集诊断信息

```bash
# 生成诊断报告
make diagnose > diagnostic_report.txt

# 包含内容：
# - 系统信息（OS, CPU, 内存, 磁盘）
# - GPU 信息
# - 配置文件检查
# - 日志文件分析
# - 依赖版本检查
```

## 安装与启动问题

### 问题 1: 依赖安装失败

**症状:**
```bash
pip install -r requirements.txt
# 报错: ERROR: Could not build wheels for xxx
```

**可能原因及解决方案:**

1. **缺少系统依赖**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install -y \
       build-essential \
       python3-dev \
       libssl-dev \
       libffi-dev \
       libxml2-dev \
       libxslt1-dev

   # CentOS/RHEL
   sudo yum install -y \
       gcc \
       gcc-c++ \
       make \
       python3-devel \
       openssl-devel \
       libffi-devel
   ```

2. **PyTorch/CUDA 版本不匹配**
   ```bash
   # 检查 CUDA 版本
   nvcc --version

   # 安装对应版本的 PyTorch
   pip install torch torchvision torchaudio \
       --index-url https://download.pytorch.org/whl/cu118
   ```

3. **网络问题**
   ```bash
   # 使用国内镜像源
   pip install -r requirements.txt \
       -i https://pypi.tuna.tsinghua.edu.cn/simple

   # 或配置代理
   pip install -r requirements.txt \
       --proxy http://proxy.example.com:8080
   ```

### 问题 2: 服务启动失败

**症状:**
```bash
python main.py
# 报错: Address already in use
```

**解决方案:**

1. **查找并终止占用端口的进程**
   ```bash
   # 查找占用 8000 端口的进程
   lsof -i :8000
   # 或
   netstat -tulpn | grep 8000

   # 终止进程
   kill -9 <PID>
   ```

2. **检查端口是否被防火墙阻止**
   ```bash
   # 检查防火墙状态
   sudo ufw status

   # 开放端口
   sudo ufw allow 8000/tcp
   ```

3. **修改配置使用其他端口**
   ```bash
   # 使用环境变量
   PORT=8080 python main.py

   # 或修改配置文件
   # config.yaml
   server:
     port: 8080
   ```

### 问题 3: Docker 容器启动失败

**症状:**
```bash
docker-compose up
# 报错: Error response from daemon
```

**解决方案:**

1. **检查 Docker 服务状态**
   ```bash
   sudo systemctl status docker
   sudo systemctl start docker
   ```

2. **清理 Docker 资源**
   ```bash
   # 清理停止的容器
   docker container prune -f

   # 清理未使用的镜像
   docker image prune -a -f

   # 清理未使用的卷
   docker volume prune -f
   ```

3. **检查磁盘空间**
   ```bash
   df -h
   # 如果 /var/lib/docker 所在分区满了，需要清理
   docker system df
   docker system prune -a --volumes -f
   ```

## 数据库相关问题

### 问题 1: 数据库连接失败

**症状:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
connection to server at "localhost" (::1), port 5432 failed:
Connection refused
```

**解决方案:**

1. **检查 PostgreSQL 服务状态**
   ```bash
   sudo systemctl status postgresql
   sudo systemctl start postgresql
   ```

2. **验证连接参数**
   ```bash
   # 测试手动连接
   psql -h localhost -U username -d database_name

   # 检查环境变量
   echo $DATABASE_URL
   # 格式: postgresql://user:password@host:port/dbname
   ```

3. **检查 PostgreSQL 认证配置**
   ```bash
   # 编辑 pg_hba.conf
   sudo nano /etc/postgresql/15/main/pg_hba.conf

   # 确保本地连接使用 md5 或 scram-sha-256 认证
   # local   all   all   md5

   # 重启 PostgreSQL
   sudo systemctl restart postgresql
   ```

### 问题 2: 数据库迁移失败

**症状:**
```
alembic upgrade head
# 报错: table "models" already exists
```

**解决方案:**

1. **检查迁移历史**
   ```bash
   # 查看迁移状态
   alembic current
   alembic history

   # 标记特定版本
   alembic stamp head
   ```

2. **清理并重新初始化（开发环境）**
   ```bash
   # 警告：会删除所有数据！
   alembic downgrade base
   alembic upgrade head
   ```

3. **手动同步迁移记录**
   ```sql
   -- 如果 alembic_version 表损坏
   DELETE FROM alembic_version;
   INSERT INTO alembic_version (version_num) VALUES ('<latest_version>');
   ```

### 问题 3: 数据库查询缓慢

**诊断步骤:**

1. **启用慢查询日志**
   ```sql
   -- PostgreSQL
   ALTER DATABASE beaverchain SET log_min_duration_statement = 1000;
   -- 记录执行超过 1 秒的查询
   ```

2. **分析查询计划**
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM models WHERE status = 'active';
   ```

3. **添加缺失的索引**
   ```sql
   -- 检查缺失的索引
   SELECT
       schemaname,
       tablename,
       indexdef
   FROM pg_indexes
   WHERE schemaname = 'public';

   -- 创建索引
   CREATE INDEX idx_models_status ON models(status);
   CREATE INDEX idx_deployments_model_id ON deployments(model_id);
   CREATE INDEX idx_inference_requests_created_at
       ON inference_requests(created_at DESC);
   ```

## 模型管理问题

### 问题 1: 模型下载失败

**症状:**
```
DownloadError: Failed to download model from Hugging Face
Connection timed out
```

**解决方案:**

1. **配置代理**
   ```bash
   export HF_ENDPOINT=https://hf-mirror.com
   export HTTP_PROXY=http://proxy.example.com:8080
   export HTTPS_PROXY=http://proxy.example.com:8080
   ```

2. **增加超时时间**
   ```python
   from huggingface_hub import snapshot_download

   snapshot_download(
       "org/model-name",
       local_dir="/models",
       cache_dir="/models/.cache",
       timeout=300,  # 5 分钟超时
       resume_download=True
   )
   ```

3. **手动下载并导入**
   ```bash
   # 手动下载到 /path/to/model
   # 然后通过 API 导入
   curl -X POST http://localhost:8000/api/v1/models/import \
        -H "Content-Type: application/json" \
        -d '{"path": "/path/to/model", "name": "my-model"}'
   ```

### 问题 2: 模型加载失败（OOM）

**症状:**
```
torch.cuda.OutOfMemoryError: CUDA out of memory
Tried to allocate 1024.00 MiB
(GPU 0; 23.65 GiB total capacity; 20.12 GiB already allocated)
```

**解决方案:**

1. **启用量化**
   ```python
   config = ModelConfig(
       model_id="large-model-70b",
       quantization="4bit",  # 4-bit 量化
       load_in_4bit=True,
       bnb_4bit_compute_dtype=torch.float16
   )
   ```

2. **启用张量并行**
   ```python
   # 使用多张 GPU
   config = ModelConfig(
       model_id="large-model-70b",
       tensor_parallel_size=4  # 使用 4 张 GPU
   )
   ```

3. **卸载不需要的模型**
   ```bash
   # 查看 GPU 内存使用
   nvidia-smi

   # 通过 API 卸载模型
   curl -X DELETE http://localhost:8000/api/v1/models/{model_id}/unload
   ```

### 问题 3: 模型版本冲突

**症状:**
```
VersionConflict: Model version mismatch.
Expected: 1.2.0, Actual: 1.1.0
```

**解决方案:**

1. **检查模型版本兼容性**
   ```bash
   curl http://localhost:8000/api/v1/models/{model_id}/versions
   ```

2. **强制重新加载**
   ```bash
   curl -X POST http://localhost:8000/api/v1/models/{model_id}/reload \
        -H "Content-Type: application/json" \
        -d '{"version": "1.2.0", "force": true}'
   ```

3. **清理模型缓存**
   ```bash
   # 删除损坏的缓存
   rm -rf /models/.cache/{model_name}

   # 重新下载
   curl -X POST http://localhost:8000/api/v1/models/{model_id}/refresh
   ```

## 部署与推理问题

### 问题 1: 模型部署超时

**症状:**
```
DeploymentTimeout: Deployment did not become ready within 300 seconds
```

**解决方案:**

1. **增加超时时间**
   ```python
   deployment = deployer.deploy(
       model_id="large-model",
       timeout_seconds=600  # 10 分钟
   )
   ```

2. **检查资源限制**
   ```yaml
   # docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 32G
         cpus: '16'
       reservations:
         devices:
           - driver: nvidia
             count: 2
             capabilities: [gpu]
   ```

3. **查看部署日志**
   ```bash
   # 查看推理容器日志
   docker logs -f <deployment-container-id>

   # 通过 API 获取部署日志
   curl http://localhost:8000/api/v1/deployments/{deployment_id}/logs
   ```

### 问题 2: 推理速度慢

**诊断:**

```python
from core.inference import benchmark

result = benchmark(
    model_id="model-123",
    batch_sizes=[1, 2, 4, 8],
    prompt_lengths=[128, 512, 1024],
    max_new_tokens=[32, 128, 512]
)

print(f"平均延迟: {result.mean_latency:.2f} ms")
print(f"吞吐量: {result.throughput:.2f} tokens/s")
```

**优化方案:**

1. **vLLM 优化**
   ```python
   config = VLLMConfig(
       gpu_memory_utilization=0.95,  # 提高 GPU 内存使用率
       max_num_batched_tokens=8192,  # 增加批处理大小
       max_num_seqs=256,             # 增加并行序列数
       enable_prefix_caching=True,    # 启用前缀缓存
       quantization="awq"             # 启用 AWQ 量化
   )
   ```

2. **批处理优化**
   ```python
   # 启用动态批处理
   config.dynamic_batching = True
   config.max_batch_wait_ns = 5000000  # 5ms 最大等待
   ```

3. **连续批处理**
   ```python
   # 使用连续批处理提高吞吐量
   config.enable_continuous_batching = True
   ```

### 问题 3: 推理结果质量差

**症状:** 输出乱码、重复、无意义

**诊断步骤:**

1. **检查提示词格式**
   ```python
   # ❌ 错误：缺少特殊标记
   prompt = "你好，介绍一下你自己"

   # ✅ 正确：使用模型要求的格式
   prompt = f"<s>[INST] {user_input} [/INST]"
   ```

2. **检查解码参数**
   ```python
   generation_config = {
       "temperature": 0.7,      # 不要太高 (0.1 - 1.0)
       "top_p": 0.9,
       "top_k": 50,
       "repetition_penalty": 1.1,  # 防止重复
       "max_new_tokens": 512,
       "do_sample": True
   }
   ```

3. **验证模型完整性**
   ```bash
   # 检查文件完整性
   sha256sum /models/model-name/*.bin
   # 与官方提供的校验和比对
   ```

## API 接口问题

### 问题 1: CORS 错误

**症状:** 浏览器控制台报错:
```
Access to fetch at 'http://api.example.com/' from origin
'http://localhost:3000' has been blocked by CORS policy
```

**解决方案:**

1. **配置 CORS 中间件**
   ```python
   # main.py
   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "http://localhost:3000",
           "https://your-domain.com"
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **使用环境变量配置**
   ```bash
   # .env
   CORS_ORIGINS=http://localhost:3000,https://your-domain.com
   ```

### 问题 2: 认证失败 (401)

**症状:**
```json
{
  "detail": "Could not validate credentials"
}
```

**解决方案:**

1. **检查 Token 格式**
   ```bash
   # ✅ 正确格式: Bearer <token>
   curl -H "Authorization: Bearer eyJhbGc..." http://...

   # ❌ 错误格式: 缺少 Bearer
   curl -H "Authorization: eyJhbGc..." http://...
   ```

2. **检查 Token 过期时间**
   ```bash
   # 解码 JWT 查看过期时间
   echo $TOKEN | cut -d "." -f2 | base64 -d | jq
   ```

3. **验证 JWT_SECRET 配置**
   ```python
   # 确认所有服务使用相同的 JWT_SECRET
   assert os.environ["JWT_SECRET"] == expected_secret
   ```

### 问题 3: 请求限流 (429)

**症状:**
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

**解决方案:**

1. **实现客户端重试**
   ```python
   import time
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(
       stop=stop_after_attempt(5),
       wait=wait_exponential(multiplier=1, min=2, max=30)
   )
   def call_api():
       response = requests.post(url, json=data)
       if response.status_code == 429:
           raise Exception("Rate limited")
       return response
   ```

2. **调整服务端限流配置**
   ```python
   # config/limits.py
   RATE_LIMITS = {
       "inference": "100/minute",  # 推理 API
       "models": "1000/minute",    # 模型管理 API
       "auth": "10/minute"         # 认证 API (更严格)
   }
   ```

## Computer-Use (CUA) 问题

### 问题 1: 模型配置错误

**症状:**
```
ModelError: Invalid combination of reasoning_effort and thinking type
medium + disabled
```

**解决方案:**

1. **检查模型兼容性**
   ```bash
   # 确认使用的模型支持多模态
   cua doctor --model
   ```

2. **禁用 reasoning_effort**
   ```yaml
   # ~/.cua/config.yaml
   model:
     reasoning_effort: null  # 设为 null 而非 "medium"
   ```

3. **切换到兼容模型**
   ```bash
   cua config model.model_id doubao-seed-code
   ```

### 问题 2: 显示环境问题

**症状:**
```
DisplayError: No display available. Set DISPLAY environment variable.
```

**解决方案:**

1. **设置虚拟显示器（Linux 无头环境）**
   ```bash
   # 安装 Xvfb
   sudo apt-get install -y xvfb

   # 启动虚拟显示器
   Xvfb :99 -screen 0 1920x1080x24 &
   export DISPLAY=:99

   # 或使用 xvfb-run
   xvfb-run -a cua run "任务描述"
   ```

2. **检查 DISPLAY 变量**
   ```bash
   echo $DISPLAY
   # 应该输出类似 :0 或 :99

   # 如果为空，设置正确的值
   export DISPLAY=:0
   ```

3. **VNC 远程查看（调试用）**
   ```bash
   # 在运行 CUA 的机器上启动 VNC
   x11vnc -display :99 -nopw -forever

   # 在本地用 VNC 客户端连接查看
   vncviewer <server-ip>:5900
   ```

### 问题 3: 浏览器启动失败

**症状:**
```
BrowserError: Failed to launch browser: timeout
```

**解决方案:**

1. **检查浏览器是否安装**
   ```bash
   # 检查 Chrome
   google-chrome --version

   # 检查 Firefox
   firefox --version
   ```

2. **以无头模式运行**
   ```python
   agent = BrowserAgent(headless=True)
   ```

3. **指定浏览器二进制路径**
   ```python
   agent = BrowserAgent(
       executable_path="/usr/bin/chromium-browser",
       headless=True
   )
   ```

4. **增加沙箱参数（Docker 环境）**
   ```python
   agent = BrowserAgent(
       chrome_options=[
           "--no-sandbox",
           "--disable-dev-shm-usage",
           "--disable-gpu"
       ]
   )
   ```

### 问题 4: 元素找不到

**症状:**
```
ElementNotFoundError: Could not find element with text "登录"
```

**解决方案:**

1. **增加等待时间**
   ```python
   # 等待最多 30 秒
   element = agent.wait_for_element(
       selector="#login",
       timeout=30
   )
   ```

2. **尝试多种定位方式**
   ```python
   # 1. CSS 选择器
   agent.click("#login-button")

   # 2. XPath
   agent.click("//button[contains(text(), '登录')]")

   # 3. 文本匹配
   agent.click_button("登录")

   # 4. 图像匹配（最后手段）
   agent.click_image("templates/login_button.png", confidence=0.8)
   ```

3. **调试：截图查看当前屏幕**
   ```python
   agent.take_screenshot("debug_current_screen.png")
   # 检查是否有弹窗遮挡、页面是否加载完成
   ```

### 问题 5: 已有 CUA 进程运行

**症状:**
```
PreflightError: existing cua run process detected
```

**解决方案:**

1. **查找并终止 CUA 进程**
   ```bash
   # 查找 CUA 进程
   ps aux | grep -i "cua"
   pkill -f "cua run"

   # 或更彻底
   pkill -9 -f "cua"
   ```

2. **清理运行目录**
   ```bash
   # 删除锁定文件
   rm -f ~/.cua/runs/*.lock

   # 查看正在运行的任务
   ls -la ~/.cua/runs/
   ```

3. **强制清除所有运行状态**
   ```bash
   cua reset --force
   ```

## 性能问题

### 问题 1: GPU 内存泄漏

**症状:** 长时间运行后 GPU 内存占用持续增长

**诊断:**
```bash
# 监控 GPU 内存使用
watch -n 1 nvidia-smi
```

**解决方案:**

1. **定期重启推理服务**
   ```yaml
   # docker-compose.yml
   deploy:
     restart_policy:
       condition: on-failure
       delay: 5s
       max_attempts: 3
       window: 120s
   ```

2. **启用内存清理**
   ```python
   import torch
   import gc

   def cleanup_gpu_memory():
       torch.cuda.empty_cache()
       gc.collect()
       torch.cuda.synchronize()

   # 每处理 N 个请求后清理
   if request_count % 100 == 0:
       cleanup_gpu_memory()
   ```

3. **监控并自动重启**
   ```python
   def check_gpu_memory(threshold=0.9):
       """检查 GPU 内存使用率，超过阈值自动重启"""
       mem_free, mem_total = torch.cuda.mem_get_info()
       usage = 1 - (mem_free / mem_total)

       if usage > threshold:
           logger.warning(f"GPU memory usage {usage:.1%}, restarting service")
           restart_inference_service()
   ```

### 问题 2: CPU 使用率过高

**症状:** CPU 使用率持续 100%

**诊断:**
```bash
# 查看 CPU 使用情况
top -H -p <PID>

# 查看调用栈
py-spy top --pid <PID>
```

**解决方案:**

1. **减少并发 worker 数量**
   ```bash
   # 减少 Celery worker
   celery -A worker.app worker --concurrency=4

   # 或启用自动伸缩
   celery -A worker.app worker --autoscale=10,2
   ```

2. **优化数据预处理**
   ```python
   # 使用多进程加速预处理
   from concurrent.futures import ProcessPoolExecutor

   def parallel_preprocess(items):
       with ProcessPoolExecutor(max_workers=4) as executor:
           results = list(executor.map(preprocess, items))
       return results
   ```

3. **启用缓存**
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=10000)
   def preprocess_text(text):
       # 耗时的预处理操作
       return tokenize(text)
   ```

### 问题 3: 磁盘 I/O 瓶颈

**症状:** 高延迟，`iostat` 显示 `%util` 接近 100%

**解决方案:**

1. **使用更快的存储**
   ```bash
   # 将模型和缓存移到 NVMe SSD
   mv /models /nvme/models
   ln -s /nvme/models /models
   ```

2. **启用文件系统缓存**
   ```bash
   # 增加 vm.dirty_ratio（谨慎使用！）
   sudo sysctl vm.dirty_ratio=50
   sudo sysctl vm.dirty_background_ratio=10
   ```

3. **使用 RAM 磁盘缓存热门模型**
   ```bash
   # 创建 64GB RAM 磁盘
   mount -t tmpfs -o size=64G tmpfs /models_cache

   # 将热门模型复制到 RAM 磁盘
   cp /models/frequently-used-model /models_cache/
   ```

## 安全与权限问题

### 问题 1: API Key 泄露

**紧急处理步骤:**

```bash
# 1. 立即撤销泄露的 Key
curl -X POST http://localhost:8000/api/v1/auth/api-keys/{key-id}/revoke

# 2. 审计日志
grep "API_KEY_HERE" /var/log/beaverchain/access.log

# 3. 生成新 Key
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
     -H "Content-Type: application/json" \
     -d '{"name": "new-key-name", "permissions": ["read", "write"]}'
```

### 问题 2: 文件上传漏洞

**症状:** 用户可以上传恶意文件

**防护措施:**

1. **文件类型验证**
   ```python
   ALLOWED_EXTENSIONS = {'.json', '.txt', '.csv', '.md'}
   MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

   def validate_upload(filename, content):
       ext = os.path.splitext(filename)[1].lower()
       if ext not in ALLOWED_EXTENSIONS:
           raise ValidationError(f"File type {ext} not allowed")

       if len(content) > MAX_FILE_SIZE:
           raise ValidationError("File too large")
   ```

2. **文件名清理**
   ```python
   import re

   def sanitize_filename(filename):
       # 移除路径字符
       filename = os.path.basename(filename)
       # 只保留安全字符
       filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
       # 限制长度
       return filename[:100]
   ```

### 问题 3: SQL 注入防护

**永远不要:**
```python
# ❌ 危险！字符串拼接
query = f"SELECT * FROM users WHERE email = '{user_input}'"

# ✅ 安全：使用参数化查询
query = "SELECT * FROM users WHERE email = %s"
cursor.execute(query, (user_input,))
```

**使用 ORM（推荐）:**
```python
# SQLAlchemy 自动防注入
user = session.query(User)\
             .filter(User.email == user_input)\
             .first()
```

## 日志与诊断

### 日志位置

```bash
# 应用日志
/var/log/beaverchain/app.log
/var/log/beaverchain/error.log

# API 访问日志
/var/log/beaverchain/access.log

# 推理服务日志
/var/log/beaverchain/inference.log

# CUA 日志
/var/log/beaverchain/cua.log

# 系统日志
/var/log/syslog                  # Ubuntu/Debian
/var/log/messages                # CentOS/RHEL
```

### 日志级别调整

```bash
# 实时调整日志级别（无需重启）
curl -X POST http://localhost:8000/api/v1/admin/log-level \
     -H "Content-Type: application/json" \
     -d '{"level": "DEBUG"}'

# 可选级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 常用日志分析命令

```bash
# 查看最近 100 行错误日志
tail -n 100 /var/log/beaverchain/error.log

# 实时查看日志
tail -f /var/log/beaverchain/app.log

# 统计各状态码数量
grep "status_code" /var/log/beaverchain/access.log | \
    awk '{print $NF}' | sort | uniq -c | sort -rn

# 查找慢请求（超过 1 秒）
grep "duration_ms" /var/log/beaverchain/access.log | \
    awk '$NF > 1000 {print $0}'

# 统计最频繁的错误
grep "ERROR" /var/log/beaverchain/error.log | \
    awk -F"Error: " '{print $2}' | sort | uniq -c | sort -rn | head -20
```

### 性能剖析

```bash
# Python 性能分析
python -m cProfile -o profile.stats main.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

# 实时 CPU 分析
py-spy top --pid <PID>

# 生成火焰图
py-spy record -o profile.svg --pid <PID>
```

## 联系支持

如果以上方案未能解决您的问题，请按照以下格式收集信息后联系技术支持：

### 问题报告模板

```
【问题标题】
简洁描述问题

【环境信息】
- 操作系统: Ubuntu 22.04
- Docker 版本: 24.0.6
- GPU: NVIDIA A100 x 8
- NVIDIA 驱动: 535.129.03
- CUDA 版本: 12.2
- BeaverChain 版本: 1.0.0
- 部署方式: docker-compose / k8s / 源码

【问题描述】
1. 预期行为是什么？
2. 实际行为是什么？
3. 复现步骤：
   - 步骤 1
   - 步骤 2
   - ...

【错误日志】
粘贴相关的错误日志（注意脱敏，移除 API Key、密码等）

【诊断信息】
运行 `make diagnose` 并粘贴输出

【配置信息】
- 相关的配置文件内容（注意脱敏）
- 使用的模型名称和版本

【截图】
如有相关截图，请附上
```

### 获取支持

- **GitHub Issues**: https://github.com/vova-byte417/BeaverChain/issues
- **文档站点**: https://docs.beaverchain.com
- **社区论坛**: https://community.beaverchain.com
- **技术支持邮箱**: support@beaverchain.com

---

**文档版本**: v1.0.0  
**最后更新**: 2024-05-13
