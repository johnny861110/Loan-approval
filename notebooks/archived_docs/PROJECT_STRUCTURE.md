# 📁 專案結構說明

本文檔詳細說明貸款審批預測 API 專案的目錄結構和文件組織。

## 🏗️ 整體架構

```
loan-approval/
├── 📱 app/                     # 核心應用程式
├── 📊 data/                    # 數據文件
├── 🤖 models/                  # 訓練好的模型
├── 📈 outputs/                 # 分析結果和報告
├── 📚 notebooks/               # Jupyter 筆記本
├── 🧪 tests/                   # 正式測試代碼
├── 📝 scripts/                 # 輔助腳本和臨時測試
├── 📖 docs/                    # 詳細文檔
├── ⚙️ config/                  # 配置文件
├── 🐳 docker-compose.yml       # Docker 部署配置
├── 📋 requirements.txt         # Python 依賴
├── ⚙️ pyproject.toml           # 專案配置 (UV)
└── 📄 README.md               # 專案主要說明
```

## 📱 核心應用程式 (`app/`)

```
app/
├── __init__.py                 # Python 包初始化
├── main.py                     # FastAPI 主程式和路由
├── model.py                    # Stacking 模型實現
├── preprocessing.py            # 數據預處理管道
├── tasks.py                    # 異步訓練任務
├── utils.py                    # 工具函數和模型管理
└── models/                     # 預訓練模型存放
```

### 關鍵文件說明

#### `main.py`
- FastAPI 應用程式入口
- 定義所有 API 端點和路由
- 包含訓練、預測、SHAP 解釋功能
- 實現異步任務狀態管理

#### `model.py`
- `StackingModel` 類實現
- 集成 LightGBM 和 XGBoost
- 支援交叉驗證和 SHAP 解釋
- 模型訓練和預測邏輯

#### `preprocessing.py`
- `DataPreprocessor` 類
- 缺失值處理和特徵編碼
- 特徵工程和標準化
- 數據驗證和清理

#### `tasks.py`
- 異步訓練任務實現
- HyperOpt 超參數優化
- 訓練進度追蹤
- 錯誤處理和日誌記錄

#### `utils.py`
- 模型保存和載入
- 文件路徑管理
- 通用工具函數

## 📊 數據目錄 (`data/`)

```
data/
└── raw/                        # 原始數據
    ├── train.csv              # 訓練數據集
    ├── test.csv               # 測試數據集
    └── sample_submission.csv   # 提交範例
```

## 🤖 模型目錄 (`models/`)

```
models/
├── best_params.json                          # 最佳超參數
├── cb_person_default_on_file_encoder_classes.json  # 編碼器類別
├── hyperopt_trials.pkl                       # HyperOpt 試驗記錄
├── loan_intent_encoder_classes.json          # 貸款意圖編碼
└── person_home_ownership_encoder_classes.json # 房屋所有權編碼
```

## 📈 輸出目錄 (`outputs/`)

```
outputs/
├── plots/                      # 視覺化圖表
│   ├── cat_feature_importances.png      # 類別特徵重要性
│   ├── lgbm_feature_importances.png     # LightGBM 特徵重要性
│   ├── roc_curve.png                    # ROC 曲線
│   └── threshold_results.png            # 閾值分析
└── reports/                    # 評估報告
    ├── complete_model_evaluation_report.json    # 完整評估報告
    ├── comprehensive_performance_analysis.json  # 性能分析
    ├── submission.csv                           # 預測結果
    ├── sweetviz_report.html                     # 數據分析報告
    └── threshold_results.csv                    # 閾值結果
```

## 📚 筆記本目錄 (`notebooks/`)

```
notebooks/
├── automl.ipynb               # AutoML 實驗
├── EDA.ipynb                  # 探索性數據分析
└── test.ipynb                 # 快速測試和驗證
```

## 🧪 測試目錄 (`tests/`)

```
tests/
├── __init__.py                # 測試包初始化
└── test_pipeline.py           # 端到端管道測試
```

## 📝 輔助腳本 (`scripts/`)

```
scripts/
├── tests/                     # 臨時測試腳本
│   ├── test_api_*.py         # API 測試腳本
│   └── test_*.ps1            # PowerShell 測試
├── check_*.py                # 檢查和驗證腳本
├── debug_*.py                # 調試腳本
├── create_*.py               # 報告生成腳本
└── *.py                      # 其他輔助腳本
```

### 腳本分類

#### 測試腳本 (`scripts/tests/`)
- `test_api_complete.py`: 完整 API 測試
- `test_api_endpoints.ps1`: PowerShell API 測試
- `test_hyperopt_optimization.py`: 超參數優化測試
- `test_model_performance.py`: 模型性能測試

#### 調試腳本
- `debug_model.py`: 模型調試
- `debug_prediction.py`: 預測調試
- `check_model_shap.py`: SHAP 檢查

#### 報告腳本
- `generate_complete_report.py`: 生成完整報告
- `create_visual_summary.py`: 創建視覺化總結
- `comprehensive_performance_analysis.py`: 性能分析

## ⚙️ 配置目錄 (`config/`)

```
config/
└── config.yaml                # 主要配置文件
```

## 📖 文檔目錄 (`docs/`)

```
docs/
└── (待添加詳細文檔)
```

## 🔧 配置文件

### `pyproject.toml`
- UV 包管理器配置
- 專案元數據和依賴
- 開發工具配置

### `requirements.txt`
- Python 依賴列表
- 適用於 pip 安裝

### `docker-compose.yml`
- Docker 容器化部署
- 服務定義和配置

### `Dockerfile`
- Docker 鏡像構建
- 環境設置和依賴安裝

## 📄 重要文檔

### 主要文檔
- `README.md`: 專案概覽和快速開始
- `QUICKSTART.md`: 5分鐘入門指南
- `API_OPTIMIZATION_SUMMARY.md`: 完整優化歷程
- `DEFAULT_PARAMS_GUIDE.md`: 默認參數指南
- `PROJECT_STRUCTURE.md`: 本文檔

### 版本控制
- `.gitignore`: Git 忽略文件配置
- `.python-version`: Python 版本指定

## 🎯 文件命名規範

### Python 文件
- **模組**: 小寫 + 下劃線 (`preprocessing.py`)
- **類**: 駝峰命名法 (`StackingModel`)
- **函數**: 小寫 + 下劃線 (`train_model_task`)

### 腳本文件
- **測試**: `test_` 前綴 (`test_api_complete.py`)
- **調試**: `debug_` 前綴 (`debug_model.py`)
- **檢查**: `check_` 前綴 (`check_shap_format.py`)
- **創建**: `create_` 前綴 (`create_visual_summary.py`)

### 數據文件
- **原始數據**: 描述性名稱 (`train.csv`, `test.csv`)
- **處理結果**: 功能性名稱 (`submission.csv`)

### 報告文件
- **JSON 報告**: 描述性名稱 (`complete_model_evaluation_report.json`)
- **圖表**: 描述性名稱 (`roc_curve.png`)

## 🚀 開發工作流程

### 1. 新功能開發
```bash
# 在 app/ 中實現核心邏輯
vim app/new_feature.py

# 在 tests/ 中添加測試
vim tests/test_new_feature.py

# 在 scripts/ 中創建測試腳本
vim scripts/test_new_feature.py
```

### 2. 模型實驗
```bash
# 在 notebooks/ 中進行實驗
jupyter notebook notebooks/experiment.ipynb

# 將成功的實驗移至 app/
mv notebook_code app/model.py
```

### 3. 部署準備
```bash
# 更新依賴
uv add new-package

# 測試完整管道
uv run python scripts/test_complete_pipeline.py

# 構建 Docker 鏡像
docker-compose build
```

## 💡 最佳實踐

### 代碼組織
1. **核心邏輯**: 放在 `app/` 目錄
2. **實驗代碼**: 放在 `notebooks/` 目錄
3. **測試代碼**: 放在 `tests/` 和 `scripts/tests/`
4. **輔助腳本**: 放在 `scripts/` 目錄

### 文件管理
1. **模型文件**: 統一放在 `models/` 目錄
2. **數據文件**: 統一放在 `data/` 目錄
3. **輸出結果**: 統一放在 `outputs/` 目錄
4. **配置文件**: 統一放在 `config/` 目錄

### 文檔維護
1. **及時更新**: 代碼變更時同步更新文檔
2. **詳細說明**: 包含使用範例和參數說明
3. **版本追蹤**: 重大變更需要版本記錄

---

**📝 備註**: 本專案結構遵循 Python 標準實踐，便於維護和擴展。
