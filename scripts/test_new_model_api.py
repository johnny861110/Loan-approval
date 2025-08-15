#!/usr/bin/env python3
"""
測試新訓練的模型
"""
import requests

def test_new_model():
    """測試新模型"""
    model_id = "model_20250815_211654_d0fdbc76"
    print(f"🎯 測試新模型: {model_id}")
    
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
        # 健康檢查
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"健康檢查: {health_response.status_code}")
        
        # 單筆預測
        response = requests.post(
            f"http://localhost:8000/v1/predict?model_id={model_id}",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 單筆預測成功!")
            print(f"  ID: {result['id']}")
            print(f"  概率: {result['probability']:.4f}")
            print(f"  標籤: {result['label']}")
            print(f"  信心: {result['confidence']:.4f}")
            
            # 測試批量預測
            print(f"\n📊 測試批量預測...")
            import pandas as pd
            
            batch_data = pd.DataFrame({
                'id': [1, 2],
                'person_age': [35, 28],
                'person_income': [60000, 45000],
                'person_home_ownership': ['RENT', 'OWN'],
                'person_emp_length': [5, 3],
                'loan_intent': ['PERSONAL', 'EDUCATION'],
                'loan_grade': ['B', 'C'],
                'loan_amnt': [10000, 8000],
                'loan_int_rate': [15.5, 18.2],
                'loan_percent_income': [0.25, 0.18],
                'cb_person_default_on_file': ['N', 'Y'],
                'cb_person_cred_hist_length': [5, 3]
            })
            
            batch_data.to_csv('test_new_model_batch.csv', index=False)
            
            with open('test_new_model_batch.csv', 'rb') as f:
                files = {'file': f}
                data = {'model_id': model_id}
                
                batch_response = requests.post(
                    "http://localhost:8000/v1/predict/batch",
                    files=files,
                    data=data,
                    timeout=15
                )
            
            if batch_response.status_code == 200:
                print("✅ 批量預測成功!")
                print(batch_response.text)
            else:
                print(f"❌ 批量預測失敗: {batch_response.status_code}")
                print(batch_response.text)
            
        else:
            print(f"❌ 單筆預測失敗: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    test_new_model()
