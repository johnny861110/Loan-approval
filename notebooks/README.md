# Notebooks 資料夾說明

## 📁 資料夾結構

### 🎯 主要 Notebooks
- `automl.ipynb` - 自動機器學習實驗
- `EDA.ipynb` - 探索性資料分析
- `test.ipynb` - 測試和實驗用途

### 📚 已歸檔的文檔 (`archived_docs/`)
存放專案開發過程中產生的各種文檔和說明：
- `API_OPTIMIZATION_SUMMARY.md` - API 優化總結
- `CLEANUP.md` - 清理指南
- `DOCKER_GUIDE.md` - Docker 使用指南
- `PRODUCTION_GUIDE.md` - 生產環境指南
- `PROJECT_STRUCTURE.md` - 專案結構說明
- `QUICKSTART.md` - 快速開始指南
- `SUMMARY.md` - 專案總結

### 🛠️ 開發腳本 (`dev_scripts/`)
存放開發和調試過程中使用的腳本：
- `check_*.py` - 模型和資料檢查腳本
- `debug_*.py` - 調試相關腳本
- `create_*.py` - 報告生成腳本
- `generate_*.py` - 內容生成腳本
- `comprehensive_performance_analysis.py` - 綜合性能分析

### 🐳 Docker 配置 (`docker_configs/`)
存放各種 Docker 相關的配置檔案：
- `docker-compose.dev.yml` - 開發環境配置
- `docker-compose.prod.yml` - 生產環境配置
- `Dockerfile.prod` - 生產環境 Dockerfile
- `deploy-prod.bat` - 生產部署腳本
- `prod-manage.bat` - 生產管理腳本
- `.env.prod.example` - 生產環境變數範例
- `nginx.conf` - Nginx 配置

## 📝 使用說明

1. **主要開發**: 使用根目錄的檔案進行日常開發
2. **歷史參考**: 需要查看開發歷史或文檔時，可參考 `archived_docs/`
3. **開發工具**: 需要調試或分析時，可使用 `dev_scripts/` 中的工具
4. **部署配置**: 需要特殊部署配置時，可參考 `docker_configs/`

## 🎯 專案結構精簡化

移動後的專案根目錄更加簡潔，主要包含：
- 核心應用程式碼 (`app/`)
- 主要配置檔案 (`config/`, `requirements.txt`)
- Docker 部署檔案 (`docker-compose.yml`, `Dockerfile`)
- 核心訓練腳本 (`scripts/`)
- 資料和模型 (`data/`, `models/`)
- 主要說明文檔 (`README.md`, `DOCKER_DEPLOYMENT_SUMMARY.md`)
