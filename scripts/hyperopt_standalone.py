#!/usr/bin/env python3
"""
本地超參數優化腳本
直接調用 tasks.py 中的超參數優化函數，無需 Celery 服務
"""

import os
import sys
import pandas as pd
import logging
from datetime import datetime
import uuid

# 添加專案根目錄到 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('hyperopt_training.log')
    ]
)

logger = logging.getLogger(__name__)


def run_standalone_hyperopt():
    """執行獨立的超參數優化（不需要 Celery）"""
    try:
        # 載入訓練資料
        logger.info("🔄 正在載入訓練資料...")
        train_data_path = "data/raw/train.csv"
        
        if not os.path.exists(train_data_path):
            raise FileNotFoundError(f"找不到訓練資料檔案: {train_data_path}")
        
        df = pd.read_csv(train_data_path)
        logger.info(f"✅ 成功載入 {len(df)} 筆訓練資料")
        logger.info(f"📊 資料形狀: {df.shape}")
        logger.info(f"📋 欄位名稱: {list(df.columns)}")
        
        # 檢查目標變數分布
        target_col = 'loan_status'
        if target_col in df.columns:
            target_dist = df[target_col].value_counts()
            logger.info("🎯 目標變數分布:")
            for label, count in target_dist.items():
                pct = count/len(df)*100
                logger.info(f"  {label}: {count} ({pct:.1f}%)")
        
        # 數據預處理
        logger.info("🔧 開始數據預處理...")
        from app.preprocessing import AdvancedDataPreprocessor
        
        preprocessor = AdvancedDataPreprocessor(create_interactions=True)
        X, y = preprocessor.fit_transform_with_target(df)
        
        logger.info(f"✅ 數據預處理完成，特徵數量: {X.shape[1]}")
        logger.info(f"📊 特徵名稱: {list(X.columns)}")
        
        # 生成唯一的任務 ID
        job_id = (f"hyperopt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                  f"_{str(uuid.uuid4())[:8]}")
        logger.info(f"🆔 任務 ID: {job_id}")
        
        # 建立任務狀態追蹤字典
        training_jobs = {
            job_id: {
                "status": "INITIALIZED",
                "created_at": datetime.now().isoformat(),
                "progress": 0,
                "message": "任務初始化..."
            }
        }
        
        # 直接調用超參數優化函數（不通過 Celery）
        logger.info("🚀 開始超參數優化...")
        from app.tasks import optimize_hyperparameters_task
        
        # 直接調用超參數優化任務
        optimization_result = optimize_hyperparameters_task(
            job_id=job_id,
            X=X,
            y=y,
            n_trials=30,  # 減少試驗次數以加快速度
            training_jobs=training_jobs
        )
        
        # 檢查優化結果
        if optimization_result and 'best_params' in optimization_result:
            logger.info("🎉 超參數優化成功完成！")
            logger.info("📊 優化結果:")
            
            best_score = optimization_result.get('best_score', 0)
            logger.info(f"  🏆 最佳 AUC 分數: {best_score:.4f}")
            
            n_trials = optimization_result.get('n_trials', 0)
            logger.info(f"  🔬 總試驗次數: {n_trials}")
            
            method = optimization_result.get('optimization_method', 'N/A')
            logger.info(f"  ⚙️ 優化方法: {method}")
            
            # 顯示最佳參數
            best_params = optimization_result['best_params']
            logger.info("🎯 最佳超參數:")
            for key, value in best_params.items():
                logger.info(f"  {key}: {value}")
            
            # 現在用最佳參數訓練完整模型
            logger.info("🚀 使用最佳參數訓練完整模型...")
            return train_final_model_with_best_params(
                df, best_params, preprocessor, job_id
            )
            
        else:
            logger.error("❌ 超參數優化失敗")
            if training_jobs[job_id]["status"] == "FAILURE":
                error_msg = training_jobs[job_id].get("message", "Unknown error")
                logger.error(f"錯誤訊息: {error_msg}")
            return None
        
    except Exception as e:
        logger.error(f"❌ 執行過程中發生錯誤: {str(e)}")
        logger.exception("詳細錯誤信息:")
        return None


def train_final_model_with_best_params(df, best_params, preprocessor, job_id):
    """使用最佳參數訓練最終模型"""
    try:
        from app.model import StackingModel
        from app.utils import save_model, generate_model_id
        from sklearn.linear_model import LogisticRegression
        
        logger.info("🔧 配置最終模型...")
        
        # 預處理數據
        X, y = preprocessor.fit_transform_with_target(df)
        
        # 創建 Stacking 模型
        stacking_model = StackingModel(cv_folds=5)
        
        # 應用最佳超參數
        logger.info("🎯 應用最佳超參數...")
        
        # 更新 LightGBM 參數
        lgb_updates = {}
        for key, value in best_params.items():
            if key.startswith('lgbm_'):
                param_name = key.replace('lgbm_', '')
                if param_name in ['n_estimators', 'num_leaves', 'max_depth',
                                  'min_child_samples']:
                    lgb_updates[param_name] = int(value)
                else:
                    lgb_updates[param_name] = value
        
        if lgb_updates:
            stacking_model.lgb_params.update(lgb_updates)
            logger.info(f"📊 LightGBM 參數已更新: {lgb_updates}")
        
        # 更新 XGBoost 參數
        xgb_updates = {}
        for key, value in best_params.items():
            if key.startswith('xgb_'):
                param_name = key.replace('xgb_', '')
                if param_name in ['n_estimators', 'max_depth', 'min_child_weight']:
                    xgb_updates[param_name] = int(value)
                else:
                    xgb_updates[param_name] = value
        
        if xgb_updates:
            stacking_model.xgb_params.update(xgb_updates)
            logger.info(f"🚀 XGBoost 參數已更新: {xgb_updates}")
        
        # 更新 Meta Model
        if 'meta_C' in best_params:
            stacking_model.meta_model = LogisticRegression(
                C=best_params['meta_C'],
                solver=best_params.get('meta_solver', 'lbfgs'),
                random_state=42,
                max_iter=1000
            )
            meta_c = best_params['meta_C']
            logger.info(f"🎯 Meta Model 參數已更新: C={meta_c}")
        
        # 訓練模型
        logger.info("🚀 開始訓練最終模型...")
        stacking_model.fit(X, y)
        logger.info("✅ 模型訓練完成")
        
        # 評估模型
        logger.info("📊 評估模型性能...")
        cv_scores = stacking_model.get_cv_scores()
        
        mean_score = cv_scores.get('mean_auc', 0)
        std_score = cv_scores.get('std_auc', 0)
        logger.info(f"🏆 交叉驗證 AUC: {mean_score:.4f} ± {std_score:.4f}")
        
        # 保存模型
        logger.info("💾 保存模型...")
        model_id = generate_model_id()
        save_model(stacking_model, preprocessor, model_id)
        
        logger.info(f"✅ 模型已保存，模型 ID: {model_id}")
        
        # 創建結果字典
        result = {
            "model_id": model_id,
            "cv_scores": cv_scores,
            "best_params": best_params,
            "feature_count": X.shape[1],
            "training_samples": len(X),
            "hyperopt_used": True,
            "completed_at": datetime.now().isoformat(),
            "job_id": job_id
        }
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 最終模型訓練失敗: {str(e)}")
        logger.exception("詳細錯誤信息:")
        return None


def check_dependencies():
    """檢查必要的依賴"""
    try:
        logger.info("🔍 正在檢查依賴套件...")
        
        # 檢查基本套件
        import pandas as pd
        import numpy as np
        import sklearn
        logger.info(f"✅ pandas: {pd.__version__}")
        logger.info(f"✅ numpy: {np.__version__}")
        logger.info(f"✅ scikit-learn: {sklearn.__version__}")
        
        # 檢查機器學習套件
        try:
            import lightgbm as lgb
            logger.info(f"✅ LightGBM: {lgb.__version__}")
        except ImportError:
            logger.error("❌ LightGBM 未安裝，請安裝: pip install lightgbm")
            return False
        
        try:
            import xgboost as xgb
            logger.info(f"✅ XGBoost: {xgb.__version__}")
        except ImportError:
            logger.error("❌ XGBoost 未安裝，請安裝: pip install xgboost")
            return False
        
        # 檢查超參數優化套件
        try:
            import hyperopt
            logger.info(f"✅ HyperOpt: {hyperopt.__version__}")
        except ImportError:
            logger.error("❌ HyperOpt 未安裝，請安裝: pip install hyperopt")
            return False
        
        # 檢查專案模組
        try:
            from app.model import StackingModel  # noqa: F401
            from app.preprocessing import AdvancedDataPreprocessor  # noqa: F401
            from app.utils import save_model, generate_model_id  # noqa: F401
            logger.info("✅ 專案模組載入成功")
        except ImportError as e:
            logger.error(f"❌ 專案模組載入失敗: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 依賴檢查失敗: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 開始獨立超參數優化程序")
    logger.info("=" * 60)
    
    # 檢查依賴
    if not check_dependencies():
        logger.error("❌ 依賴檢查失敗，程序終止")
        sys.exit(1)
    
    logger.info("=" * 60)
    
    # 執行超參數優化
    result = run_standalone_hyperopt()
    
    logger.info("=" * 60)
    
    if result is not None:
        logger.info("🎉 程序執行完成")
        logger.info(f"🆔 模型 ID: {result.get('model_id', 'N/A')}")
        
        cv_scores = result.get('cv_scores', {})
        if cv_scores:
            mean_auc = cv_scores.get('mean_auc', 0)
            logger.info(f"🏆 最終 AUC 分數: {mean_auc:.4f}")
    else:
        logger.error("❌ 程序執行失敗")
        sys.exit(1)
