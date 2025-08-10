# 🐳 Docker 快速啟動指南

本指南將幫助您使用 Docker 快速啟動貸款審批預測系統。

## 📋 前置要求

### 必備軟體
- **Docker Desktop**: 20.10+ [下載連結](https://www.docker.com/products/docker-desktop)
- **Docker Compose**: 2.0+ (通常隨 Docker Desktop 安裝)

### 系統要求
- **記憶體**: 最低 4GB，建議 8GB+
- **磁碟空間**: 最低 5GB 可用空間
- **CPU**: 最低 2 核心，建議 4 核心+

## 🚀 一鍵啟動

### 1. 克隆專案
```bash
git clone https://github.com/johnny861110/Loan-approval.git
cd Loan-approval
```

### 2. 啟動服務
```bash
# Windows
docker-manage.bat up

# 或直接使用 docker-compose
docker-compose up -d
```

### 3. 驗證服務
```bash
# 檢查服務狀態
docker-manage.bat status

# 查看服務日誌
docker-manage.bat logs
```

## 🎯 可用環境

### 🔧 開發環境
```bash
# 啟動開發環境（包含代碼熱重載）
docker-manage.bat dev

# 或
docker-compose -f docker-compose.dev.yml up -d
```

**開發環境特色:**
- ✅ 代碼熱重載
- ✅ 詳細日誌輸出
- ✅ 可選的 Flower 監控
- ✅ 掛載本地代碼目錄

### 🏭 生產環境
```bash
# 啟動生產環境
docker-manage.bat prod

# 或
docker-compose -f docker-compose.prod.yml up -d
```

**生產環境特色:**
- ✅ Nginx 反向代理
- ✅ 多工作程序
- ✅ 資源限制
- ✅ 監控和觀測

## 🔗 服務端點

### 🌐 主要服務
| 服務 | URL | 說明 |
|------|-----|------|
| API 文檔 | http://localhost:8000/docs | Swagger UI |
| API Redoc | http://localhost:8000/redoc | ReDoc UI |
| 健康檢查 | http://localhost:8000/health | 服務狀態 |

### 📊 監控服務 (可選)
| 服務 | URL | 說明 |
|------|-----|------|
| Flower | http://localhost:5555 | Celery 任務監控 |
| Grafana | http://localhost:3000 | 儀表板 |
| Prometheus | http://localhost:9090 | 指標收集 |

## 🛠️ 常用操作

### 基本命令
```bash
# 構建映像
docker-manage.bat build

# 啟動所有服務
docker-manage.bat up

# 停止所有服務
docker-manage.bat down

# 查看服務狀態
docker-manage.bat status

# 查看日誌
docker-manage.bat logs

# 查看特定服務日誌
docker-manage.bat logs api
docker-manage.bat logs worker
docker-manage.bat logs redis
```

### 清理操作
```bash
# 完全清理（停止服務、刪除容器、網路、掛載）
docker-manage.bat clean

# 手動清理
docker-compose down -v
docker system prune -f
```

## 🎮 API 使用範例

### 1. 健康檢查
```bash
curl http://localhost:8000/health
```

### 2. 訓練模型
```bash
curl -X POST "http://localhost:8000/train" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/train_70_percent.csv"
```

### 3. 單筆預測
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "person_age": 25,
    "person_income": 50000,
    "person_emp_length": 2,
    "loan_amnt": 10000,
    "loan_int_rate": 8.5,
    "loan_percent_income": 0.2,
    "cb_person_cred_hist_length": 5,
    "person_home_ownership": "RENT",
    "loan_intent": "PERSONAL",
    "loan_grade": "B",
    "cb_person_default_on_file": "N"
  }'
```

### 4. 批量預測
```bash
curl -X POST "http://localhost:8000/batch_predict" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_predict_with_id.csv"
```

## 🔍 故障排除

### 常見問題

#### 1. 端口衝突
```bash
# 檢查端口使用情況
netstat -an | findstr :8000
netstat -an | findstr :6379

# 修改 docker-compose.yml 中的端口映射
ports:
  - "8001:8000"  # 改為其他端口
```

#### 2. 記憶體不足
```bash
# 監控資源使用
docker stats

# 在 docker-compose.yml 中調整資源限制
deploy:
  resources:
    limits:
      memory: 1G
```

#### 3. 映像構建失敗
```bash
# 清理快取重新構建
docker-manage.bat clean
docker-manage.bat build

# 檢查 Dockerfile 和依賴
docker build . --no-cache -t loan-approval:debug
```

#### 4. 服務無法啟動
```bash
# 檢查詳細日誌
docker-compose logs api
docker-compose logs worker
docker-compose logs redis

# 檢查 Docker 服務狀態
docker version
docker-compose version
```

### 日誌分析
```bash
# 實時查看所有服務日誌
docker-compose logs -f

# 查看最近的日誌
docker-compose logs --tail=50

# 保存日誌到文件
docker-compose logs > docker-logs.txt
```

## 📁 目錄結構

### Docker 相關檔案
```
├── Dockerfile              # 基本開發環境
├── Dockerfile.prod         # 生產環境優化版本
├── docker-compose.yml      # 基本服務編排
├── docker-compose.dev.yml  # 開發環境配置
├── docker-compose.prod.yml # 生產環境配置
├── .dockerignore           # Docker 忽略檔案
├── docker-manage.bat       # Windows 管理腳本
├── docker-manage.sh        # Linux/macOS 管理腳本
└── nginx.conf              # Nginx 配置（生產環境）
```

### 掛載目錄
```
├── app/models/             # 模型檔案持久化
├── data/                   # 數據檔案
├── logs/                   # 應用程式日誌
└── outputs/                # 輸出檔案（報告、圖表等）
```

## 🔒 安全考量

### 生產環境建議
1. **環境變數**: 使用 `.env` 檔案管理敏感配置
2. **網路隔離**: 使用自定義 Docker 網路
3. **資源限制**: 設定記憶體和 CPU 限制
4. **健康檢查**: 啟用所有服務的健康檢查
5. **SSL/TLS**: 在生產環境中啟用 HTTPS

### 開發環境注意事項
1. **端口暴露**: 僅暴露必要的端口
2. **數據掛載**: 注意本地數據的安全性
3. **日誌輸出**: 避免在日誌中暴露敏感資訊

## 📈 性能優化

### 映像優化
- 使用多階段構建減少映像大小
- 合理安排 Dockerfile 層次以利用快取
- 清理不必要的檔案和依賴

### 運行時優化
- 根據硬體調整工作程序數量
- 配置適當的記憶體限制
- 使用 Redis 進行快取和任務佇列

### 監控和觀測
- 啟用 Prometheus 指標收集
- 配置 Grafana 儀表板
- 使用 Flower 監控 Celery 任務

## 📞 支援和幫助

如果遇到問題，請檢查：
1. [Docker 官方文檔](https://docs.docker.com/)
2. [FastAPI 文檔](https://fastapi.tiangolo.com/)
3. [專案 README](README.md)
4. [故障排除指南](TROUBLESHOOTING.md)

或在專案的 GitHub Issues 中提交問題。
