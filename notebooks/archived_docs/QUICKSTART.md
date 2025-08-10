# 🚀 5分鐘快速開始指南

歡迎使用貸款審批預測系統！本指南將帶您從零開始，在 5 分鐘內體驗完整的機器學習 API 服務。

## 🎯 學習目標

完成本指南後，您將能夠：
- ✅ 啟動 API 服務並訪問互動式文檔
- ✅ 訓練一個高精度的貸款預測模型
- ✅ 進行單筆和批量預測
- ✅ 查看模型性能和解釋性分析

## 📋 前置要求

### 系統要求
```bash
# 檢查 Python 版本
python --version  # 需要 >= 3.9

# 檢查可用記憶體
wmic computersystem get TotalPhysicalMemory  # 建議 >= 8GB
```

### 必備工具
- 🐍 **Python 3.9+**: 現代 Python 環境
- 📦 **UV**: 現代 Python 包管理器 (推薦)
- 💻 **終端機**: PowerShell/CMD/Git Bash

### 安裝 UV (如果尚未安裝)
```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 驗證安裝
uv --version
```

## ⚡ 三步驟啟動

### 第一步：取得專案

```bash
# 克隆專案
git clone https://github.com/johnny861110/Loan-approval.git
cd Loan-approval

# 檢查專案結構
dir  # Windows
ls   # Linux/Mac
```

### 第二步：安裝環境

**🎉 使用 UV (推薦 - 速度更快):**

```bash
# 一鍵安裝所有依賴
uv sync

# 驗證安裝
uv run python -c "import fastapi, lightgbm, xgboost; print('✅ 依賴安裝成功!')"
```

**或使用傳統 pip:**

```bash
pip install -r requirements.txt
```

### 3. 啟動服務

```bash
# 使用 UV
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# 或直接運行
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. 驗證服務

打開瀏覽器訪問: <http://localhost:8000/docs>

## 🧪 快速測試

### 使用 API 文檔進行測試

1. 訪問 <http://localhost:8000/docs>
2. 找到 `GET /v1/models` 端點
3. 點擊 "Try it out" 並執行
4. 確認返回可用模型列表

### 命令行測試

```bash
# 檢查服務健康狀態
curl http://localhost:8000/health

# 獲取模型列表
curl http://localhost:8000/v1/models

# 進行預測 (需要先有訓練好的模型)
curl -X POST "http://localhost:8000/v1/predict?model_id=your_model_id" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "person_age": 35,
    "person_income": 75000,
    "person_home_ownership": "OWN",
    "person_emp_length": 8,
    "loan_intent": "PERSONAL",
    "loan_grade": "A",
    "loan_amnt": 10000,
    "loan_int_rate": 7.5,
    "loan_percent_income": 0.13,
    "cb_person_default_on_file": "N",
    "cb_person_cred_hist_length": 12
  }'
```

## 🎯 訓練您的第一個模型

### 1. 準備數據

確保您的 CSV 檔案包含以下欄位：

- `id`: 唯一識別碼
- `person_age`: 申請人年齡
- `person_income`: 年收入
- `person_home_ownership`: 房屋擁有狀況 (RENT/OWN/MORTGAGE)
- `person_emp_length`: 就業年數
- `loan_intent`: 貸款用途
- `loan_grade`: 貸款等級 (A-G)
- `loan_amnt`: 貸款金額
- `loan_int_rate`: 利率
- `loan_percent_income`: 貸款收入比
- `cb_person_default_on_file`: 是否有違約記錄 (Y/N)
- `cb_person_cred_hist_length`: 信用歷史長度
- `loan_status`: 目標變數 (0=核准, 1=拒絕)

### 2. 啟動訓練

```bash
curl -X POST "http://localhost:8000/v1/train/start" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_training_data.csv" \
  -F "use_hyperopt=true" \
  -F "cv_folds=5"
```

### 3. 監控訓練進度

```bash
# 替換 {job_id} 為實際的任務ID
curl "http://localhost:8000/v1/train/status/{job_id}"
```

## 🐳 Docker 快速部署

### 1. 使用 Docker Compose (最簡單)

```bash
docker-compose up -d
```

### 2. 或使用 Docker

```bash
# 構建映像
docker build -t loan-approval .

# 運行容器
docker run -d -p 8000:8000 --name loan-api loan-approval
```

### 3. 驗證部署

```bash
curl http://localhost:8000/health
```

## 📊 使用 Jupyter Notebooks

### 1. 啟動 Jupyter

```bash
# 使用 UV
uv run jupyter lab

# 或直接啟動
jupyter lab
```

### 2. 探索範例筆記本

- `notebooks/EDA.ipynb`: 探索性數據分析
- `notebooks/automl.ipynb`: AutoML 實驗
- `notebooks/test.ipynb`: 模型測試

## 🔧 常見問題

### Q: 服務啟動失敗？

A: 確認端口 8000 未被占用，或修改為其他端口：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Q: 模型訓練太慢？

A: 調整超參數優化試驗次數：

```bash
curl -X POST "http://localhost:8000/v1/train/start" \
  -F "file=@data.csv" \
  -F "use_hyperopt=true" \
  -F "n_trials=10"  # 減少試驗次數
```

### Q: 內存不足？

A: 減少交叉驗證折數：

```bash
curl -X POST "http://localhost:8000/v1/train/start" \
  -F "file=@data.csv" \
  -F "cv_folds=3"  # 從5減少到3
```

## 🎉 下一步

恭喜！您已經成功啟動了貸款核准預測系統。

接下來建議：

1. **閱讀完整文檔**: 查看 [API_GUIDE.md](docs/API_GUIDE.md)
2. **探索範例**: 參考 [EXAMPLES.md](docs/EXAMPLES.md)  
3. **了解專案**: 閱讀 [PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)
4. **自定義模型**: 使用您自己的數據訓練模型
5. **整合應用**: 將 API 整合到您的應用程式中

## 🆘 需要幫助？

- 查看 [API 文檔](http://localhost:8000/docs)
- 閱讀 [完整文檔](docs/)
- 提交 [Issue](https://github.com/your-username/Loan-approval/issues)

---

💡 **提示**: 建議在生產環境中使用 Docker 部署，並配置適當的資源限制和監控。
