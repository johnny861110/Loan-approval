#!/usr/bin/env python3
"""
測試特定模型的腳本
"""
import requests
import pandas as pd

def test_specific_model(model_id):
    """測試特定模型"""
    print(f"🎯 測試模型: {model_id}")
    
    # 測試數據
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
    
    try:
        # 單筆預測
        response = requests.post(
            f"http://localhost:8000/v1/predict?model_id={model_id}",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 單筆預測成功:")
            print(f"  概率: {result['probability']:.4f}")
            print(f"  標籤: {result['label']}")
            return True
        else:
            print(f"❌ 單筆預測失敗: {response.status_code}")
            print(f"錯誤: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def main():
    """主函數"""
    # 測試我們之前確認工作的模型
    working_models = [
        "model_20250815_204558_dfd4d9c0",  # 之前測試成功的模型
        "model_20250815_204411_11639a3a",
        "model_20250815_204335_69618b72",
        "model_20250815_202840_053f845b"
    ]
    
    print("🧪 測試不同模型的相容性\n")
    
    success_count = 0
    for model_id in working_models:
        if test_specific_model(model_id):
            success_count += 1
        print()
    
    print(f"📊 結果: {success_count}/{len(working_models)} 個模型成功")
    
    if success_count > 0:
        print("✅ 找到可用的模型！")
    else:
        print("❌ 所有模型都有問題，需要重新訓練")

if __name__ == "__main__":
    main()
