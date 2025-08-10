# 🚀 生產環境部署指南

本指南將幫助您將貸款審批預測系統部署到生產環境。

## 📋 前置要求

### 系統要求
- **操作系統**: Linux/Windows Server/macOS
- **記憶體**: 最低 8GB，建議 16GB+
- **磁碟空間**: 最低 20GB 可用空間
- **CPU**: 最低 4 核心，建議 8 核心+

### 必備軟體
- **Docker**: 20.10+ 
- **Docker Compose**: 2.0+
- **Git**: 最新版本

## 🛠️ 快速部署

### 1. 克隆專案
```bash
git clone https://github.com/johnny861110/Loan-approval.git
cd Loan-approval
```

### 2. 配置環境變數
```bash
# 複製環境變數範本
copy .env.prod.example .env.prod

# 編輯配置檔案 (重要！)
notepad .env.prod
```

### 3. 部署服務
```bash
# Windows
deploy-prod.bat

# Linux/macOS
chmod +x deploy-prod.sh
./deploy-prod.sh
```

### 4. 驗證部署
```bash
# 檢查服務狀態
prod-manage.bat status

# 健康檢查
prod-manage.bat health
```

## 🏗️ 架構概覽

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   FastAPI       │    │     Redis       │
│  (反向代理)      │────│   (API 服務)     │────│   (任務佇列)     │
│   Port: 80/443  │    │   Port: 8000    │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │  Celery Worker  │
                       │   (背景任務)     │
                       └─────────────────┘
```

## 🔧 服務管理

### 基本操作
```bash
# 啟動服務
prod-manage.bat start

# 停止服務
prod-manage.bat stop

# 重啟服務
prod-manage.bat restart

# 查看狀態
prod-manage.bat status
```

### 日誌監控
```bash
# 查看所有服務日誌
prod-manage.bat logs

# 查看特定服務日誌
prod-manage.bat logs api
prod-manage.bat logs worker
prod-manage.bat logs redis
```

### 服務更新
```bash
# 自動更新和重新部署
prod-manage.bat update
```

## 📊 監控和觀測

### 啟用監控服務
```bash
prod-manage.bat monitor
```

### 監控服務
- **Flower** (Celery 監控): http://localhost:5555
- **Prometheus** (指標收集): http://localhost:9090
- **Grafana** (儀表板): http://localhost:3000

### 健康檢查端點
- **API 健康**: http://localhost/health
- **API 文檔**: http://localhost/docs
- **API 指標**: http://localhost/metrics

## 🔒 安全配置

### 1. 環境變數安全
```bash
# 確保 .env.prod 檔案權限正確
chmod 600 .env.prod

# 重要配置項目：
SECRET_KEY=          # 強密碼
REDIS_PASSWORD=      # Redis 密碼
DATABASE_URL=        # 資料庫連接
```

### 2. SSL/TLS 配置
```bash
# 將 SSL 證書放在 ssl/ 目錄
mkdir ssl/
# 複製您的證書檔案
# cert.pem -> ssl/cert.pem
# key.pem -> ssl/key.pem

# 修改 nginx.conf 啟用 HTTPS
```

### 3. 防火牆配置
```bash
# 僅開放必要端口
# 80 (HTTP)
# 443 (HTTPS)
# 22 (SSH，管理用)
```

## 📈 性能優化

### 1. 資源配置
在 `docker-compose.prod.yml` 中調整：
```yaml
deploy:
  resources:
    limits:
      memory: 2G      # 根據實際需要調整
      cpus: '1.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

### 2. 快取配置
```bash
# Redis 記憶體配置
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### 3. 工作程序調整
```bash
# FastAPI 工作程序數量 (建議: CPU 核心數 * 2)
CMD ["uvicorn", "app.main:app", "--workers", "8"]

# Celery 工作程序並發數
command: celery -A app.tasks worker --concurrency=4
```

## 🛠️ 故障排除

### 常見問題

#### 1. 服務無法啟動
```bash
# 檢查 Docker 服務
docker version

# 檢查日誌
docker-compose -f docker-compose.prod.yml logs

# 檢查磁碟空間
df -h
```

#### 2. API 無回應
```bash
# 檢查 Nginx 配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 檢查 API 容器狀態
docker-compose -f docker-compose.prod.yml ps api

# 重啟 API 服務
docker-compose -f docker-compose.prod.yml restart api
```

#### 3. 記憶體不足
```bash
# 監控資源使用
docker stats

# 調整服務資源限制
# 編輯 docker-compose.prod.yml
```

### 日誌收集
```bash
# 收集所有日誌
mkdir logs/$(date +%Y%m%d)
docker-compose -f docker-compose.prod.yml logs > logs/$(date +%Y%m%d)/services.log

# 系統日誌
dmesg > logs/$(date +%Y%m%d)/system.log
```

## 🔄 備份和還原

### 自動備份
```bash
# 執行備份
prod-manage.bat backup

# 設定定期備份 (Windows Task Scheduler)
schtasks /create /tn "LoanApproval-Backup" /tr "C:\path\to\prod-manage.bat backup" /sc daily /st 02:00
```

### 數據還原
```bash
# 停止服務
prod-manage.bat stop

# 還原模型檔案
docker run --rm -v loan-approval_app_models:/data -v $(pwd)/backup:/backup alpine sh -c "cd /data && tar -xzf /backup/models.tar.gz"

# 重啟服務
prod-manage.bat start
```

## 🚀 擴展部署

### 負載均衡
```yaml
# docker-compose.prod.yml
api:
  deploy:
    replicas: 3  # 多個 API 實例
```

### 外部資料庫
```bash
# 使用 PostgreSQL
DATABASE_URL=postgresql://user:password@external-db:5432/loanapproval
```

### 雲端部署
- **AWS**: ECS, EKS, Elastic Beanstalk
- **Azure**: Container Instances, AKS
- **GCP**: Cloud Run, GKE

## 📞 支援和維護

### 監控指標
- **回應時間**: < 200ms (p95)
- **可用性**: > 99.9%
- **記憶體使用**: < 80%
- **CPU 使用**: < 70%

### 定期維護
- 每週檢查日誌
- 每月更新依賴套件
- 每季度安全審查
- 每年災難復原演練

### 聯絡資訊
- **技術支援**: tech-support@company.com
- **緊急聯絡**: emergency@company.com
- **文檔更新**: docs@company.com
