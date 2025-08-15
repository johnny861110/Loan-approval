#!/usr/bin/env python3
"""
調試 API 預處理時的特徵數量
"""

from app.utils import load_model
import pandas as pd

def debug_api_preprocessing():
    """調試 API 預處理時的特徵數量"""
    
    # 獲取最新模型
    model_id = "model_20250815_212421_83c40bf4"
    
    print(f"調試模型: {model_id}")
    
    # 加載模型和預處理器
    model_data = load_model(model_id)
    preprocessor = model_data['preprocessor']
    
    print(f"預處理器類型: {type(preprocessor)}")
    print(f"保存的特徵數量: {len(preprocessor.get_feature_names())}")
    
    # 創建與 API 測試相同的輸入數據
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
    
    # 移除 id 字段（就像 API 中做的一樣）
    input_data = test_data.copy()
    input_data.pop('id', None)
    input_df = pd.DataFrame([input_data])
    
    print(f"輸入數據形狀: {input_df.shape}")
    print(f"輸入欄位: {list(input_df.columns)}")
    
    # 進行預處理
    X_processed = preprocessor.transform(input_df)
    
    print(f"處理後數據形狀: {X_processed.shape}")
    print(f"處理後欄位數: {len(X_processed.columns) if hasattr(X_processed, 'columns') else 'N/A'}")
    
    if hasattr(X_processed, 'columns'):
        print("處理後欄位列表:")
        for i, col in enumerate(X_processed.columns):
            print(f"  {i+1:2d}. {col}")
    
    # 檢查是否有 id 欄位
    if hasattr(X_processed, 'columns') and 'id' in X_processed.columns:
        print("警告: 處理後的數據包含 id 欄位")
        X_for_prediction = X_processed.drop('id', axis=1)
        print(f"移除 id 後的數據形狀: {X_for_prediction.shape}")
    else:
        X_for_prediction = X_processed
        print("處理後的數據不包含 id 欄位")

if __name__ == "__main__":
    debug_api_preprocessing()
