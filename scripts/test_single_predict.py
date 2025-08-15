#!/usr/bin/env python3
"""
直接測試單筆預測
"""
import requests
import pandas as pd

def test_single_prediction():
    """直接測試單筆預測"""
    
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
    
    # 獲取最新模型
    print("獲取最新模型...")
    response = requests.get("http://localhost:8001/v1/models", timeout=10)
    if response.status_code == 200:
        models = response.json()['models']
        latest_model = sorted(models, key=lambda x: x['created_at'], reverse=True)[0]
        model_id = latest_model['model_id']
        print(f"最新模型: {model_id}")
    else:
        print(f"獲取模型失敗: {response.status_code}")
        return
    
    # 測試預測
    print("測試預測...")
    response = requests.post(
        f"http://localhost:8001/v1/predict?model_id={model_id}",
        json=test_data,
        timeout=10
    )
    
    print(f"狀態碼: {response.status_code}")
    print(f"響應: {response.text}")

if __name__ == "__main__":
    test_single_prediction()
