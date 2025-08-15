# 🚀 貸款審批系統 - 快速開始指南

## 📋 系統概覽

這是一個基於機器學習的貸款審批預測系統，使用 Docker 容器化部署，提供 REST API 接口進行貸款申請的自動化審批預測。

## 🐳 Docker Hub 映像

系統已推送到 Docker Hub，可以直接使用：

- **API 服務**: `johnny861110/loan-approval-api:latest`
- **Worker 服務**: `johnny861110/loan-approval-worker:latest`
- **版本標籤**: `v1.0.0`, `latest`

### 🚀 一鍵啟動（推薦）

```bash
# 1. 下載生產環境配置
curl -o docker-compose.prod.yml https://raw.githubusercontent.com/johnny861110/Loan-approval/main/docker-compose.prod.yml

# 2. 啟動所有服務
docker-compose -f docker-compose.prod.yml up -d

# 3. 檢查服務狀態
docker-compose -f docker-compose.prod.yml ps

# 4. 測試 API
curl http://localhost:8000/health
```

### 🏗️ 系統架構
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │    │   Redis Broker  │    │ Celery Worker   │
│   Port: 8000    │◄──►│   Port: 6379    │◄──►│  Background     │
│   (預測服務)     │    │   (訊息代理)     │    │  Tasks          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ 系統需求

### 必要環境
- **Docker**: 20.10+ 
- **Docker Compose**: 2.0+
- **作業系統**: Windows 10/11, macOS, Linux
- **記憶體**: 至少 4GB RAM
- **磁碟空間**: 至少 3GB 可用空間

### 檢查環境
```bash
# 檢查 Docker 版本
docker --version

# 檢查 Docker Compose 版本
docker-compose --version

# 確認 Docker 服務運行中
docker info
```

## 🚀 快速啟動

### 1️⃣ 獲取專案代碼
```bash
# 克隆倉庫
git clone https://github.com/johnny861110/Loan-approval.git
cd Loan-approval
```

### 2️⃣ 啟動服務
```bash
# 一鍵啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps
```

### 3️⃣ 驗證服務
```bash
# 檢查 API 健康狀態
curl http://localhost:8000/health

# 查看服務日誌
docker-compose logs -f
```

## 📊 服務狀態檢查

### 健康檢查
所有服務啟動後應顯示為 `healthy` 狀態：

```bash
$ docker-compose ps
NAME                     STATUS
loan-approval-api-1      Up (healthy)
loan-approval-redis-1    Up (healthy)  
loan-approval-worker-1   Up (healthy)
```

### 預期回應
API 健康檢查應返回：
```json
{
  "status": "healthy",
  "timestamp": "2025-08-11T08:00:00.000000",
  "available_models": 12
}
```

## 🎯 API 使用指南

### 📖 API 文檔
啟動服務後，訪問 API 文檔：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 🔑 主要端點

#### 1. 健康檢查
```bash
GET http://localhost:8000/health
```

#### 2. 單筆預測
```bash
POST http://localhost:8000/predict
Content-Type: application/json

{
  "person_age": 30,
  "person_income": 50000,
  "person_home_ownership": "RENT",
  "person_emp_length": 5,
  "loan_intent": "PERSONAL",
  "loan_grade": "B",
  "loan_amnt": 10000,
  "loan_int_rate": 12.5,
  "loan_percent_income": 0.2,
  "cb_person_default_on_file": "N",
  "cb_person_cred_hist_length": 8
}
```

#### 3. 批次預測
```bash
POST http://localhost:8000/batch_predict
Content-Type: multipart/form-data

# 上傳 CSV 檔案
file: loan_applications.csv
```

### 📝 範例請求

#### cURL 範例
```bash
# 單筆預測
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "person_age": 25,
    "person_income": 45000,
    "person_home_ownership": "RENT",
    "person_emp_length": 3,
    "loan_intent": "EDUCATION",
    "loan_grade": "C",
    "loan_amnt": 15000,
    "loan_int_rate": 15.2,
    "loan_percent_income": 0.33,
    "cb_person_default_on_file": "N",
    "cb_person_cred_hist_length": 5
  }'
```

#### Python 範例
```python
import requests
import json

# API 端點
url = "http://localhost:8000/predict"

# 申請資料
data = {
    "person_age": 35,
    "person_income": 75000,
    "person_home_ownership": "MORTGAGE",
    "person_emp_length": 8,
    "loan_intent": "HOMEIMPROVEMENT",
    "loan_grade": "A",
    "loan_amnt": 20000,
    "loan_int_rate": 8.5,
    "loan_percent_income": 0.27,
    "cb_person_default_on_file": "N",
    "cb_person_cred_hist_length": 12
}

# 發送請求
response = requests.post(url, json=data)
result = response.json()

print(f"預測結果: {result['prediction']}")
print(f"違約機率: {result['probability']:.2%}")
```

## 📁 資料格式說明

### 輸入欄位定義

| 欄位名稱 | 類型 | 描述 | 範例值 |
|---------|------|------|--------|
| `person_age` | 整數 | 申請人年齡 | 25-80 |
| `person_income` | 整數 | 年收入 | 20000-150000 |
| `person_home_ownership` | 字串 | 房屋擁有狀況 | "RENT", "OWN", "MORTGAGE" |
| `person_emp_length` | 整數 | 就業年數 | 0-20 |
| `loan_intent` | 字串 | 貸款目的 | "PERSONAL", "EDUCATION", "MEDICAL", "VENTURE", "HOMEIMPROVEMENT", "DEBTCONSOLIDATION" |
| `loan_grade` | 字串 | 貸款等級 | "A", "B", "C", "D", "E", "F", "G" |
| `loan_amnt` | 整數 | 貸款金額 | 1000-50000 |
| `loan_int_rate` | 浮點數 | 利率 (%) | 5.0-25.0 |
| `loan_percent_income` | 浮點數 | 貸款收入比 | 0.1-1.0 |
| `cb_person_default_on_file` | 字串 | 是否有違約記錄 | "Y", "N" |
| `cb_person_cred_hist_length` | 整數 | 信用歷史長度 | 1-30 |

### 輸出格式
```json
{
  "prediction": 0,
  "prediction_label": "核准",
  "probability": 0.85,
  "model_version": "v1.0",
  "processed_at": "2025-08-11T08:00:00Z"
}
```

## 🔧 進階操作

### 服務管理

#### 啟動和停止
```bash
# 啟動所有服務
docker-compose up -d

# 停止所有服務  
docker-compose down

# 重啟特定服務
docker-compose restart api

# 查看服務日誌
docker-compose logs -f api
docker-compose logs -f worker
```

#### 擴展服務
```bash
# 擴展 Worker 數量
docker-compose up -d --scale worker=3

# 檢查擴展結果
docker-compose ps
```

### 監控和除錯

#### 日誌查看
```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f api

# 查看最近 100 行日誌
docker-compose logs --tail=100 worker
```

#### 進入容器調試
```bash
# 進入 API 容器
docker exec -it loan-approval-api-1 bash

# 進入 Worker 容器
docker exec -it loan-approval-worker-1 bash

# 檢查 Celery 狀態
docker exec loan-approval-worker-1 celery -A app.tasks inspect active
```

### 效能調優

#### 調整 Worker 並發
編輯 `docker-compose.yml`：
```yaml
worker:
  command: celery -A app.tasks worker --loglevel=info --concurrency=4
```

#### 調整記憶體限制
```yaml
api:
  deploy:
    resources:
      limits:
        memory: 2G
      reservations:
        memory: 1G
```

## 📋 測試數據

### 範例 CSV 檔案
創建 `test_data.csv`：
```csv
person_age,person_income,person_home_ownership,person_emp_length,loan_intent,loan_grade,loan_amnt,loan_int_rate,loan_percent_income,cb_person_default_on_file,cb_person_cred_hist_length
25,45000,RENT,3,EDUCATION,C,15000,15.2,0.33,N,5
35,75000,MORTGAGE,8,HOMEIMPROVEMENT,A,20000,8.5,0.27,N,12
28,38000,RENT,2,PERSONAL,D,8000,18.5,0.21,Y,3
```

## 🚨 故障排除

### 常見問題

#### 1. 容器啟動失敗
```bash
# 檢查 Docker 服務
docker info

# 重新構建映像
docker-compose build --no-cache

# 清理並重啟
docker-compose down
docker system prune -f
docker-compose up -d
```

#### 2. API 無法連接
```bash
# 檢查端口是否被佔用
netstat -an | findstr :8000

# 檢查防火牆設置
# Windows: 確認 8000 端口未被阻擋
# Linux: sudo ufw allow 8000
```

#### 3. Worker 無法處理任務
```bash
# 檢查 Redis 連接
docker exec loan-approval-worker-1 ping redis

# 檢查 Celery 狀態
docker exec loan-approval-worker-1 celery -A app.tasks inspect ping
```

#### 4. 記憶體不足
```bash
# 檢查系統資源
docker stats

# 減少 Worker 並發數
# 編輯 docker-compose.yml 中的 --concurrency 參數
```

### 日誌分析

#### 錯誤日誌位置
- API 日誌: `docker-compose logs api`
- Worker 日誌: `docker-compose logs worker`
- Redis 日誌: `docker-compose logs redis`

#### 常見錯誤碼
- `500`: 內部服務器錯誤 - 檢查模型檔案
- `422`: 請求參數錯誤 - 檢查輸入格式
- `503`: 服務不可用 - 檢查依賴服務

## 🔒 安全建議

### 生產環境部署
1. **更改默認端口**
2. **啟用 HTTPS**
3. **設置防火牆規則**
4. **使用環境變數管理敏感資訊**
5. **定期更新映像**

### 存取控制
```yaml
# 添加到 docker-compose.yml
api:
  environment:
    - API_KEY=${API_KEY}
    - ALLOWED_HOSTS=${ALLOWED_HOSTS}
```

## 📚 參考資源

### 相關文檔
- [Docker 官方文檔](https://docs.docker.com/)
- [FastAPI 文檔](https://fastapi.tiangolo.com/)
- [Celery 文檔](https://docs.celeryproject.org/)

### 支援聯絡
- **GitHub Issues**: https://github.com/johnny861110/Loan-approval/issues
- **專案維護者**: johnny861110

---

## 🎉 開始使用

現在你已經準備好使用貸款審批系統了！

1. ✅ 啟動服務: `docker-compose up -d`
2. ✅ 訪問 API 文檔: http://localhost:8000/docs  
3. ✅ 測試預測功能
4. ✅ 整合到你的應用程式中

祝你使用愉快！🚀
