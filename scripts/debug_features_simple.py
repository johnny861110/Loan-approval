#!/usr/bin/env python3
"""
簡化版特徵調試腳本
"""

from app.utils import load_model
from app.preprocessing import DataPreprocessor
import pandas as pd
import os
from datetime import datetime

def debug_features_simple():
    """簡化版特徵調試"""
    
    # 1. 獲取最新模型
    models_dir = "app/models"
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
                "created_at": created_time
            })
    
    latest_model = sorted(models, key=lambda x: x['created_at'], reverse=True)[0]
    model_id = latest_model['model_id']
    
    print(f"最新模型: {model_id}")
    
    # 2. 加載模型並檢查預處理器
    try:
        model_data = load_model(model_id)
        print("模型數據鍵:", list(model_data.keys()))
        
        if 'preprocessor' in model_data:
            preprocessor = model_data['preprocessor']
            print(f"預處理器類型: {type(preprocessor)}")
            
            if hasattr(preprocessor, 'get_feature_names'):
                saved_features = preprocessor.get_feature_names()
                print(f"保存的特徵數量: {len(saved_features)}")
                print("保存的特徵列表:")
                for i, feature in enumerate(saved_features):
                    print(f"  {i+1:2d}. {feature}")
            else:
                print("預處理器沒有 get_feature_names 方法")
                
    except Exception as e:
        print(f"錯誤: {e}")
        return
    
    print("\n=== 檢查當前預處理器特徵 ===")
    
    # 3. 創建新的預處理器並檢查特徵
    new_preprocessor = DataPreprocessor()
    
    # 創建測試數據
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
    
    # 擬合新預處理器
    new_preprocessor.fit(test_df)
    current_features = new_preprocessor.get_feature_names()
    
    print(f"當前預處理器特徵數量: {len(current_features)}")
    print("當前預處理器特徵列表:")
    for i, feature in enumerate(current_features):
        print(f"  {i+1:2d}. {feature}")
    
    # 4. 比較差異
    if 'preprocessor' in model_data and hasattr(model_data['preprocessor'], 'get_feature_names'):
        saved_features = model_data['preprocessor'].get_feature_names()
        
        print(f"\n=== 特徵比較 ===")
        print(f"保存的特徵數: {len(saved_features)}")
        print(f"當前特徵數: {len(current_features)}")
        
        saved_set = set(saved_features)
        current_set = set(current_features)
        
        missing_in_current = saved_set - current_set
        extra_in_current = current_set - saved_set
        
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
    debug_features_simple()
