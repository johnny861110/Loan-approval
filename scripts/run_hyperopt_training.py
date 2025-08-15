#!/usr/bin/env python3
"""
使用 tasks.py 中的超參數優化功能訓練模型
這個腳本會直接調用 tasks.py 中的函數，而不需要 Celery 服務
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


def run_hyperopt_training():
    """執行超參數優化訓練"""
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
                logger.info(f"  {label}: {count} ({count/len(df)*100:.1f}%)")
        
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
        
        # 直接匯入並調用超參數優化任務
        logger.info("🚀 開始執行超參數優化訓練...")
        
        # 直接匯入 tasks 模組中的訓練函數
        from app.tasks import train_model_task
        
        # 執行帶有超參數優化的模型訓練
        result = train_model_task(
            job_id=job_id,
            df=df,
            use_hyperopt=True,  # 啟用超參數優化
            cv_folds=5,
            training_jobs=training_jobs
        )
        
        # 檢查訓練結果
        if training_jobs[job_id]["status"] == "SUCCESS":
            logger.info("🎉 超參數優化訓練成功完成！")
            
            result_info = training_jobs[job_id].get("result", {})
            
            if result_info:
                logger.info("📊 訓練結果:")
                model_id = result_info.get('model_id', 'N/A')
                logger.info(f"  🆔 模型 ID: {model_id}")
                
                cv_scores = result_info.get('cv_scores', 'N/A')
                logger.info(f"  � 交叉驗證分數: {cv_scores}")
                
                feature_count = result_info.get('feature_count', 'N/A')
                logger.info(f"  � 特徵數量: {feature_count}")
                
                training_samples = result_info.get('training_samples', 'N/A')
                logger.info(f"  🔢 訓練樣本數: {training_samples}")
                
                hyperopt_used = result_info.get('hyperopt_used', 'N/A')
                logger.info(f"  ⚙️ 使用超參數優化: {hyperopt_used}")
                
                completed_at = result_info.get('completed_at', 'N/A')
                logger.info(f"  📅 完成時間: {completed_at}")
                
                # 如果有優化參數，顯示最佳參數
                optimized_params = result_info.get('optimized_params')
                if optimized_params:
                    logger.info("🎯 最佳超參數:")
                    for key, value in optimized_params.items():
                        logger.info(f"  {key}: {value}")
            
            logger.info("💾 模型已保存到 models/ 目錄")
            
        else:
            logger.error("❌ 超參數優化訓練失敗")
            error_msg = training_jobs[job_id].get('message', 'Unknown error')
            logger.error(f"錯誤訊息: {error_msg}")
            if 'error' in training_jobs[job_id]:
                logger.error(f"詳細錯誤: {training_jobs[job_id]['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 執行過程中發生錯誤: {str(e)}")
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
            logger.warning("⚠️ LightGBM 未安裝")
        
        try:
            import xgboost as xgb
            logger.info(f"✅ XGBoost: {xgb.__version__}")
        except ImportError:
            logger.warning("⚠️ XGBoost 未安裝")
        
        # 檢查超參數優化套件
        try:
            import hyperopt
            logger.info(f"✅ HyperOpt: {hyperopt.__version__}")
        except ImportError:
            logger.warning("⚠️ HyperOpt 未安裝，將無法進行超參數優化")
        
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
    logger.info("🚀 開始超參數優化訓練程序")
    logger.info("=" * 60)
    
    # 檢查依賴
    if not check_dependencies():
        logger.error("❌ 依賴檢查失敗，程序終止")
        sys.exit(1)
    
    logger.info("=" * 60)
    
    # 執行訓練
    result = run_hyperopt_training()
    
    logger.info("=" * 60)
    
    if result is not None:
        logger.info("🎉 程序執行完成")
    else:
        logger.error("❌ 程序執行失敗")
        sys.exit(1)
