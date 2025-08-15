#!/usr/bin/env python3
"""
API 測試腳本
"""
import requests
import pandas as pd
import json
import time

def test_health():
    """測試健康狀態"""
    print("🔍 測試健康狀態...")
    try:
        response = requests.get("http://localhost:8001/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康檢查失敗: {e}")
        return False

def test_models():
    """測試模型列表"""
    print("\n📋 測試模型列表...")
    try:
        response = requests.get("http://localhost:8001/v1/models", timeout=10)
        if response.status_code == 200:
            models = response.json()['models']
            print(f"✅ 找到 {len(models)} 個模型")
            
            # 顯示最新的 5 個模型
            latest_models = sorted(models, key=lambda x: x['created_at'], reverse=True)[:5]
            print("最新模型:")
            for model in latest_models:
                print(f"  - {model['model_id']} ({model['created_at']})")
            
            return latest_models[0]['model_id'] if latest_models else None
        else:
            print(f"❌ 獲取模型列表失敗: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 獲取模型列表失敗: {e}")
        return None

def test_single_prediction(model_id):
    """測試單筆預測"""
    print(f"\n🎯 測試單筆預測 (模型: {model_id})...")
    
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
        response = requests.post(
            f"http://localhost:8001/v1/predict?model_id={model_id}",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 預測成功:")
            print(f"  ID: {result['id']}")
            print(f"  模型: {result['model_id']}")
            print(f"  概率: {result['probability']:.4f}")
            print(f"  標籤: {result['label']}")
            print(f"  信心: {result['confidence']:.4f}")
            return True
        else:
            print(f"❌ 單筆預測失敗: {response.status_code}")
            print(f"響應: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 單筆預測失敗: {e}")
        return False

def test_batch_prediction(model_id):
    """測試批量預測"""
    print(f"\n📊 測試批量預測 (模型: {model_id})...")
    
    # 創建測試數據
    test_data = pd.DataFrame({
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
    
    # 保存為 CSV
    csv_file = 'test_batch_api.csv'
    test_data.to_csv(csv_file, index=False)
    print(f"創建測試檔案: {csv_file}")
    
    try:
        with open(csv_file, 'rb') as f:
            files = {'file': f}
            data = {'model_id': model_id}
            
            response = requests.post(
                "http://localhost:8001/v1/predict/batch",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            print("✅ 批量預測成功:")
            print(response.text)
            return True
        else:
            print(f"❌ 批量預測失敗: {response.status_code}")
            print(f"響應: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 批量預測失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始 API 測試\n")
    
    # 1. 健康檢查
    if not test_health():
        print("❌ 服務器未響應，退出測試")
        return
    
    # 2. 獲取最新模型
    latest_model = test_models()
    if not latest_model:
        print("❌ 無法獲取模型，退出測試")
        return
    
    # 3. 測試單筆預測
    single_success = test_single_prediction(latest_model)
    
    # 4. 測試批量預測
    batch_success = test_batch_prediction(latest_model)
    
    # 總結
    print(f"\n📋 測試總結:")
    print(f"健康檢查: ✅")
    print(f"模型列表: ✅")
    print(f"單筆預測: {'✅' if single_success else '❌'}")
    print(f"批量預測: {'✅' if batch_success else '❌'}")
    
    if single_success and batch_success:
        print("\n🎉 所有測試通過！")
    else:
        print("\n⚠️ 部分測試失敗，需要進一步檢查")

if __name__ == "__main__":
    main()
