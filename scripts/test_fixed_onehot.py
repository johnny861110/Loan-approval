#!/usr/bin/env python3
"""
測試新的固定 One-Hot 編碼預處理器
"""

import pandas as pd
from app.preprocessing import DataPreprocessor, AdvancedDataPreprocessor

def test_fixed_onehot_preprocessor():
    """測試固定 One-Hot 編碼預處理器"""
    
    print("🧪 測試固定 One-Hot 編碼預處理器...")
    
    # 創建測試數據
    test_data = {
        "id": [1, 2],
        "person_age": [35, 28],
        "person_income": [60000, 45000],
        "person_home_ownership": ["RENT", "OWN"],
        "person_emp_length": [5, 3],
        "loan_intent": ["PERSONAL", "EDUCATION"],
        "loan_grade": ["B", "C"],
        "loan_amnt": [10000, 8000],
        "loan_int_rate": [15.5, 18.2],
        "loan_percent_income": [0.25, 0.18],
        "cb_person_default_on_file": ["N", "Y"],
        "cb_person_cred_hist_length": [5, 3]
    }
    
    test_df = pd.DataFrame(test_data)
    print(f"測試數據形狀: {test_df.shape}")
    print("測試數據:")
    print(test_df)
    
    # 測試基本預處理器
    print("\n=== 測試基本 DataPreprocessor ===")
    basic_preprocessor = DataPreprocessor()
    basic_preprocessor.fit(test_df)
    
    print(f"特徵數量: {len(basic_preprocessor.get_feature_names())}")
    print("特徵列表:")
    for i, feature in enumerate(basic_preprocessor.get_feature_names()):
        print(f"  {i+1:2d}. {feature}")
    
    # 轉換測試
    basic_transformed = basic_preprocessor.transform(test_df)
    print(f"轉換後形狀: {basic_transformed.shape}")
    
    # 測試進階預處理器
    print("\n=== 測試進階 AdvancedDataPreprocessor ===")
    advanced_preprocessor = AdvancedDataPreprocessor(create_interactions=True)
    advanced_preprocessor.fit(test_df)
    
    print(f"特徵數量: {len(advanced_preprocessor.get_feature_names())}")
    print("特徵列表:")
    for i, feature in enumerate(advanced_preprocessor.get_feature_names()):
        print(f"  {i+1:2d}. {feature}")
    
    # 轉換測試
    advanced_transformed = advanced_preprocessor.transform(test_df)
    print(f"轉換後形狀: {advanced_transformed.shape}")
    
    # 測試單筆數據
    print("\n=== 測試單筆預測數據 ===")
    single_data = {
        "id": 999,
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
    
    single_df = pd.DataFrame([single_data])
    print("單筆數據:")
    print(single_df)
    
    # 使用進階預處理器轉換
    single_transformed = advanced_preprocessor.transform(single_df)
    print(f"轉換後形狀: {single_transformed.shape}")
    print(f"特徵數量: {single_transformed.shape[1]}")
    
    print("\n✅ 測試完成！")

if __name__ == "__main__":
    test_fixed_onehot_preprocessor()
