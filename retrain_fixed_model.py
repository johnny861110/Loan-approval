#!/usr/bin/env python3
"""
使用修正後的預處理器重新訓練模型
"""

import os
import sys
import pandas as pd
import logging
from datetime import datetime

# 添加專案根目錄到 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.model import StackingModel
from app.preprocessing import AdvancedDataPreprocessor
from app.utils import save_model, generate_model_id

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def retrain_fixed_model():
    """使用修正後的預處理器重新訓練模型"""
    try:
        logger.info("🚀 開始使用修正後的預處理器重新訓練模型")
        
        # 載入訓練資料
        logger.info("📥 載入訓練資料...")
        df = pd.read_csv("data/raw/train.csv")
        logger.info(f"✅ 載入 {len(df)} 筆訓練資料")
        
        # 建立修正後的預處理器
        logger.info("🔧 建立進階預處理器...")
        preprocessor = AdvancedDataPreprocessor(create_interactions=True)
        
        # 預處理資料
        logger.info("⚙️ 預處理資料...")
        X, y = preprocessor.fit_transform_with_target(df)
        
        logger.info(f"✅ 預處理完成")
        logger.info(f"📊 特徵數量: {X.shape[1]}")
        logger.info(f"📋 特徵名稱數量: {len(preprocessor.get_feature_names())}")
        logger.info(f"🔍 特徵數量匹配: {X.shape[1] == len(preprocessor.get_feature_names())}")
        
        # 建立 Stacking 模型
        logger.info("🏗️ 建立 Stacking 模型...")
        stacking_model = StackingModel(cv_folds=5, random_state=42)
        
        # 訓練模型
        logger.info("🚀 開始訓練模型...")
        stacking_model.fit(X, y)
        
        # 獲取性能指標
        cv_scores = stacking_model.get_cv_scores()
        logger.info("📊 模型性能:")
        logger.info(f"  AUC: {cv_scores.get('mean_auc', 'N/A'):.4f}")
        logger.info(f"  準確率: {cv_scores.get('mean_accuracy', 'N/A'):.4f}")
        
        # 生成模型 ID 並保存
        model_id = generate_model_id()
        save_model(stacking_model, preprocessor, model_id)
        
        logger.info(f"✅ 模型重新訓練完成！")
        logger.info(f"🆔 新模型 ID: {model_id}")
        logger.info(f"📊 特徵數量: {X.shape[1]}")
        
        return model_id
        
    except Exception as e:
        logger.error(f"❌ 模型重新訓練失敗: {str(e)}")
        raise

if __name__ == "__main__":
    retrain_fixed_model()
