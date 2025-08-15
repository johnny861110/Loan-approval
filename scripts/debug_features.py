#!/usr/bin/env python3
"""
調試特徵不匹配問題
"""

from app.utils import load_model
from app.preprocessing import DataPreprocessor
import pandas as pd
import os
from datetime import datetime

def debug_feature_mismatch():
    """調試特徵不匹配問題"""
    
    # 1. 檢查最新模型的特徵
    print("=== 檢查模型特徵 ===")
    
    # 獲取所有模型
    models_dir = "app/models"
    if not os.path.exists(models_dir):
        print("模型目錄不存在")
        return
    
    models = []
    for filename in os.listdir(models_dir):
        if filename.endswith('.pkl'):
            model_id = filename.replace('.pkl', '')
            model_path = os.path.join(models_dir, filename)
            created_time = datetime.fromtimestamp(
                os.path.getctime(model_path)
            ).isoformat()
            
            models.append({
                "model_id": model_id,
                "created_at": created_time,
                "file_size": os.path.getsize(model_path)
            })
    
    latest_model = sorted(models, key=lambda x: x['created_at'], reverse=True)[0]
    model_id = latest_model['model_id']
    
    print(f"最新模型: {model_id}")
    
    # 加載模型獲取詳細信息
    try:
        model_info = load_model(model_id)
        if 'features' in model_info:
            model_features = model_info['features']
            print(f"模型特徵列表數量: {len(model_features)}")
            print("模型特徵列表:")
            for i, feature in enumerate(model_features):
                print(f"  {i+1:2d}. {feature}")
        else:
            print("模型信息中沒有特徵列表")
            return
    except Exception as e:
        print(f"加載模型失敗: {e}")
        return
    
    print("\n=== 檢查當前預處理器特徵 ===")
    
    # 2. 檢查當前預處理器生成的特徵
    preprocessor = DataPreprocessor()
    
    # 創建測試數據（與API測試相同的數據）
    test_data = {
        "id": 1,
        "person_age": 35,
        "person_income": 60000,
        "person_home_ownership": "RENT",
        "person_emp_length": 5,
        "loan_intent": "PERSONAL",
        "loan_grade": "B",
        "loan_amnt": 10000,
        "loan_int_rate": 15.5,
        "loan_percent_income": 0.25,
        "cb_person_default_on_file": "N",
        "cb_person_cred_hist_length": 5
    }
    
    test_df = pd.DataFrame([test_data])
    print(f"測試數據欄位數: {len(test_df.columns)}")
    print("測試數據欄位:", list(test_df.columns))
    
    # 擬合預處理器
    preprocessor.fit(test_df)
    current_features = preprocessor.get_feature_names()
    
    print(f"當前預處理器特徵數量: {len(current_features)}")
    print("當前預處理器特徵列表:")
    for i, feature in enumerate(current_features):
        print(f"  {i+1:2d}. {feature}")
    
    print("\n=== 特徵比較 ===")
    print(f"模型特徵數: {len(model_features)}")
    print(f"當前特徵數: {len(current_features)}")
    
    # 找出差異
    model_set = set(model_features)
    current_set = set(current_features)
    
    missing_in_current = model_set - current_set
    extra_in_current = current_set - model_set
    
    if missing_in_current:
        print(f"\n當前缺少的特徵 ({len(missing_in_current)} 個):")
        for feature in sorted(missing_in_current):
            print(f"  - {feature}")
    
    if extra_in_current:
        print(f"\n當前多出的特徵 ({len(extra_in_current)} 個):")
        for feature in sorted(extra_in_current):
            print(f"  + {feature}")
    
    if not missing_in_current and not extra_in_current:
        print("✅ 特徵完全匹配！")
    else:
        print("❌ 特徵不匹配！")

if __name__ == "__main__":
    debug_feature_mismatch()
