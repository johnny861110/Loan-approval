#!/usr/bin/env python3
"""
測試新模型訓練腳本
"""

import pandas as pd
import sys
import os

# 添加 app 目錄到路徑
sys.path.append('app')

from app.preprocessing import AdvancedDataPreprocessor
from app.model import StackingModel
from app.utils import save_model

def main():
    print("開始訓練新模型...")
    
    # 載入訓練數據
    train_data_path = 'data/train_70_percent.csv'
    if not os.path.exists(train_data_path):
        print(f"訓練數據不存在: {train_data_path}")
        return
    
    print(f"載入訓練數據: {train_data_path}")
    df = pd.read_csv(train_data_path)
    print(f"數據形狀: {df.shape}")
    print(f"欄位: {list(df.columns)}")
    
    # 數據預處理
    print("\n開始數據預處理...")
    preprocessor = AdvancedDataPreprocessor(create_interactions=True)
    
    # 分離特徵和目標
    X_features = df.drop(columns=['loan_status'])  # 移除目標列
    y = df['loan_status']
    
    # 訓練預處理器
    preprocessor.fit(X_features)
    X_processed = preprocessor.transform(X_features)
    
    # 移除 id 欄位（如果存在）用於模型訓練
    if 'id' in X_processed.columns:
        X_for_training = X_processed.drop('id', axis=1)
        print(f"移除 id 欄位後的特徵數: {X_for_training.shape[1]}")
    else:
        X_for_training = X_processed
    
    print(f"預處理後特徵數: {X_processed.shape[1]}")
    print(f"模型訓練特徵數: {X_for_training.shape[1]}")
    print(f"預處理器特徵名稱數量: {len(preprocessor.feature_names)}")
    
    # 訓練模型
    print("\n開始訓練 Stacking 模型...")
    model = StackingModel(cv_folds=3, random_state=42)
    model.fit(X_for_training, y)
    
    # 保存模型
    from datetime import datetime
    import uuid
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    model_id = f"model_{timestamp}_{unique_id}"
    
    model_path = save_model(model, preprocessor, model_id)
    print(f"\n模型訓練完成，模型 ID: {model_id}")
    print(f"模型保存位置: {model_path}")
    
    # 測試預測
    print("\n測試預測功能...")
    test_data = {
        'person_age': 35,
        'person_income': 60000,
        'person_home_ownership': 'RENT',
        'person_emp_length': 5,
        'loan_intent': 'PERSONAL',
        'loan_grade': 'B',
        'loan_amnt': 10000,
        'loan_int_rate': 15.5,
        'loan_percent_income': 0.25,
        'cb_person_default_on_file': 'N',
        'cb_person_cred_hist_length': 5
    }
    
    test_df = pd.DataFrame([test_data])
    X_test = preprocessor.transform(test_df)
    
    # 移除 id 欄位（如果存在）
    if 'id' in X_test.columns:
        X_test_for_pred = X_test.drop('id', axis=1)
    else:
        X_test_for_pred = X_test
    
    print(f"測試數據轉換後形狀: {X_test.shape}")
    print(f"用於預測的形狀: {X_test_for_pred.shape}")
    
    try:
        prob = model.predict_proba(X_test_for_pred)
        print(f"預測成功！機率: {prob[0]:.4f}")
    except Exception as e:
        print(f"預測失敗: {e}")

if __name__ == "__main__":
    main()
