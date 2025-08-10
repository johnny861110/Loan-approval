# 🏦 Loan Approval Prediction API

一個企業級的貸款審批預測系統，基於先進的機器學習技術，提供高精度的風險評估和自動化決策支持。

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 核心特性

### 🤖 智能預測引擎

- **Stacking Ensemble**: 結合 LightGBM 和 XGBoost 的集成學習
- **高精度**: 準確率達 95.8%，ROC-AUC 達 97.84%
- **快速響應**: 平均預測時間 1.08ms/筆

### 🔧 自動化機器學習

- **HyperOpt 優化**: 自動超參數調優，50+ 試驗尋找最佳參數
- **交叉驗證**: 5-fold CV 確保模型穩定性
- **特徵工程**: 自動創建交互特徵和數據預處理

### 🚀 生產就緒 API

- **REST API**: 完整的 CRUD 操作和批量處理
- **異步處理**: 支援背景訓練和狀態監控
- **模型管理**: 多版本模型並存，動態切換

### 📊 可解釋性分析

- **SHAP 整合**: 提供全局和局部特徵重要性
- **業務指標**: 混淆矩陣、ROC 曲線、風險分析
- **視覺化報告**: 自動生成評估報告和圖表

## 🚀 快速開始

### 前置需求

```bash
# 確保已安裝 Python 3.9+ 和 UV
python --version  # >= 3.9
uv --version      # 最新版本
```

### 一鍵安裝

```bash
# 克隆專案
git clone https://github.com/johnny861110/Loan-approval.git
cd Loan-approval

# 安裝依賴（UV 會自動創建虛擬環境）
uv sync

# 啟動 API 服務
uv run python -m app.main
```

API 服務會在 <http://localhost:8000> 啟動，訪問 <http://localhost:8000/docs> 查看互動式文檔。

## 📖 使用指南

### 1️⃣ 模型訓練

```bash
# 使用完整的超參數優化訓練
curl -X POST "http://localhost:8000/v1/train/start" \
  -F "file=@data/raw/train.csv" \
  -F "use_hyperopt=true" \
  -F "cv_folds=5"

# 返回 job_id，用於查詢訓練狀態
```

### 2️⃣ 監控訓練

```bash
# 查看訓練進度
curl "http://localhost:8000/v1/train/status/{job_id}"

# 訓練完成後會返回 model_id
```

### 3️⃣ 模型預測

```bash
# 批量預測
curl -X POST "http://localhost:8000/v1/predict/batch" \
  -F "file=@data/raw/test.csv" \
  -F "model_id={model_id}"

# 單筆預測
curl -X POST "http://localhost:8000/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "person_age": 30,
    "person_income": 50000,
    "person_emp_length": 5,
    "loan_amnt": 10000,
    "loan_int_rate": 12.5,
    "loan_percent_income": 0.2,
    "cb_person_cred_hist_length": 8,
    "person_home_ownership": "RENT",
    "loan_intent": "PERSONAL",
    "loan_grade": "B",
    "cb_person_default_on_file": "N"
  }' \
  -G -d "model_id={model_id}"
```

### 4️⃣ 模型解釋

```bash
# 獲取全局特徵重要性
curl "http://localhost:8000/v1/shap/global?model_id={model_id}"

# 獲取單筆預測解釋
curl -X POST "http://localhost:8000/v1/shap/local" \
  -F "file=@single_record.csv" \
  -F "model_id={model_id}"
```

## 📁 專案架構

```
loan-approval/
├── 📱 app/                     # 核心應用程式
│   ├── main.py                 # FastAPI 主程式
│   ├── model.py                # Stacking 模型實現
│   ├── preprocessing.py        # 數據預處理管道
│   ├── tasks.py                # 訓練任務管理
│   └── utils.py                # 工具函數
├── 📊 data/                    # 數據文件
│   └── raw/                    # 原始數據
│       ├── train.csv           # 訓練數據
│       ├── test.csv            # 測試數據
│       └── sample_submission.csv
├── 🤖 models/                  # 訓練好的模型
├── 📈 outputs/                 # 分析結果
│   ├── plots/                  # 視覺化圖表
│   └── reports/                # 評估報告
├── 📚 notebooks/               # Jupyter 筆記本
├── 🧪 tests/                   # 測試代碼
├── 📝 scripts/                 # 輔助腳本
├── 📖 docs/                    # 詳細文檔
├── 🐳 docker-compose.yml       # Docker 部署
├── 📋 requirements.txt         # 依賴列表
└── ⚙️ pyproject.toml           # 專案配置
```

## 🎯 模型性能

| 指標 | 數值 | 說明 |
|------|------|------|
| **準確率** | 95.8% | 整體預測準確性 |
| **ROC-AUC** | 0.9784 | 分類效果優秀 |
| **精確率** | 95.7% | 正例預測準確性 |
| **召回率** | 95.8% | 正例識別完整性 |
| **F1 分數** | 95.6% | 精確率與召回率平衡 |

### 業務指標

- **正常還款識別**: 99.1% 召回率
- **違約識別**: 75.2% 召回率  
- **預測速度**: 1.08ms/筆
- **漏判違約**: 24.8%（需要業務權衡）

## 🛠️ 開發指南

### 本地開發

```bash
# 激活開發環境
uv shell

# 安裝開發依賴
uv add --dev pytest black flake8

# 運行測試
uv run pytest tests/

# 代碼格式化
uv run black app/
```

### Docker 部署

```bash
# 構建鏡像
docker-compose build

# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f
```

## 📚 文檔與資源

- 📖 [快速開始指南](QUICKSTART.md)
- 🔧 [API 優化指南](API_OPTIMIZATION_SUMMARY.md)
- 📊 [模型評估報告](outputs/reports/)
- 🎯 [默認參數指南](DEFAULT_PARAMS_GUIDE.md)

## 🤝 貢獻指南

我們歡迎社區貢獻！請遵循：

- 代碼風格：使用 Black 格式化
- 測試：確保所有測試通過
- 文檔：更新相關文檔
- 提交：使用清晰的提交訊息

## 📄 許可證

本專案採用 MIT 許可證 - 詳見 [LICENSE](LICENSE) 文件。

## 🆘 支持與反饋

- 🐛 **問題回報**: [GitHub Issues](https://github.com/johnny861110/Loan-approval/issues)
- 💡 **功能請求**: [GitHub Discussions](https://github.com/johnny861110/Loan-approval/discussions)
- 📧 **聯絡方式**: johnny861110@example.com

---

**💡 提示**: 這是一個演示專案，實際部署前請確保遵守相關的數據保護和金融法規。
