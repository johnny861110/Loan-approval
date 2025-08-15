# Docker Hub 部署指南

## 映像信息

本專案已推送到 Docker Hub，包含以下映像：

### 1. API 服務映像
- **倉庫**: `johnny861110/loan-approval-api`
- **標籤**: 
  - `latest` - 最新版本
  - `v1.0.0` - 版本 1.0.0

### 2. Worker 服務映像
- **倉庫**: `johnny861110/loan-approval-worker`
- **標籤**:
  - `latest` - 最新版本  
  - `v1.0.0` - 版本 1.0.0

## 快速部署

### 使用 Docker Compose

1. 創建 `docker-compose.prod.yml` 文件：

```yaml
services:
  # FastAPI 主應用
  api:
    image: johnny861110/loan-approval-api:latest
    ports:
      - "8000:8000"
    volumes:
      - ./app/models:/app/app/models
      - ./data:/app/data
      - ./logs:/app/logs
      - ./outputs:/app/outputs
    environment:
      - PYTHONPATH=/app
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
      - MPLCONFIGDIR=/tmp/matplotlib
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # Celery Worker
  worker:
    image: johnny861110/loan-approval-worker:latest
    volumes:
      - ./app/models:/app/app/models
      - ./data:/app/data
      - ./logs:/app/logs
      - ./outputs:/app/outputs
    environment:
      - PYTHONPATH=/app
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
      - MPLCONFIGDIR=/tmp/matplotlib
    depends_on:
      - redis
    restart: unless-stopped

  # Redis (用於 Celery 任務佇列)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

2. 啟動服務：

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 單獨運行映像

#### 運行 API 服務

```bash
# 啟動 Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 啟動 API 服務
docker run -d \
  --name loan-approval-api \
  -p 8000:8000 \
  -e REDIS_URL=redis://redis:6379/0 \
  -e ENVIRONMENT=production \
  --link redis:redis \
  johnny861110/loan-approval-api:latest
```

#### 運行 Worker 服務

```bash
docker run -d \
  --name loan-approval-worker \
  -e REDIS_URL=redis://redis:6379/0 \
  -e ENVIRONMENT=production \
  --link redis:redis \
  johnny861110/loan-approval-worker:latest
```

## 環境變數配置

### 必要環境變數

- `REDIS_URL`: Redis 連接 URL（默認: `redis://redis:6379/0`）
- `PYTHONPATH`: Python 路徑（默認: `/app`）
- `ENVIRONMENT`: 運行環境（`development`/`production`）

### 可選環境變數

- `MPLCONFIGDIR`: Matplotlib 配置目錄（默認: `/tmp/matplotlib`）
- `UV_CACHE_DIR`: UV 快取目錄（默認: `/tmp/uv-cache`）

## 數據持久化

建議掛載以下目錄來持久化數據：

- `./app/models:/app/app/models` - 模型文件
- `./data:/app/data` - 數據文件  
- `./logs:/app/logs` - 日誌文件
- `./outputs:/app/outputs` - 輸出文件

## 健康檢查

API 服務提供健康檢查端點：

```bash
curl http://localhost:8000/health
```

預期回應：
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T...",
  "available_models": 0
}
```

## 監控和日誌

### 查看服務狀態

```bash
# 使用 Docker Compose
docker-compose -f docker-compose.prod.yml ps

# 單獨查看
docker ps
```

### 查看日誌

```bash
# API 服務日誌
docker logs loan-approval-api

# Worker 服務日誌  
docker logs loan-approval-worker

# 使用 Docker Compose
docker-compose -f docker-compose.prod.yml logs -f api
```

## 擴展部署

### 水平擴展 Worker

```bash
# 擴展到 3 個 worker 實例
docker-compose -f docker-compose.prod.yml up -d --scale worker=3
```

### 負載均衡

可以使用 Nginx 或其他負載均衡器來分發 API 請求：

```nginx
upstream loan_approval_api {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://loan_approval_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 安全注意事項

1. **網路安全**: 在生產環境中，建議使用 Docker 網路隔離服務
2. **環境變數**: 敏感信息應使用 Docker secrets 或外部配置管理
3. **映像掃描**: 定期掃描映像中的安全漏洞
4. **更新策略**: 定期更新基礎映像和依賴項

## 故障排除

### 常見問題

1. **連接 Redis 失敗**: 檢查 Redis 服務是否運行，網路連接是否正常
2. **記憶體不足**: 調整 Docker 記憶體限制或優化模型大小
3. **端口衝突**: 確保指定端口未被其他服務佔用

### 除錯模式

```bash
# 以互動模式運行 API 服務進行除錯
docker run -it \
  --rm \
  -p 8000:8000 \
  -e ENVIRONMENT=development \
  johnny861110/loan-approval-api:latest \
  /bin/bash
```

## 版本管理

### 標籤策略

- `latest`: 最新穩定版本
- `v1.0.0`: 語意化版本標籤
- `dev`: 開發版本（如有）

### 更新部署

```bash
# 拉取最新映像
docker pull johnny861110/loan-approval-api:latest
docker pull johnny861110/loan-approval-worker:latest

# 重新啟動服務
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```
