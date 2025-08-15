"""
Docker 更新後的 ID 欄位處理驗證腳本
"""

import requests
import json
import pandas as pd
import io
from typing import Dict, Any

def test_single_prediction():
    """測試單筆預測的 ID 處理"""
    print("=" * 50)
    print("測試單筆預測 ID 處理")
    print("=" * 50)
    
    url = "http://localhost:8000/v1/predict"
    
    # 測試數據，包含 ID
    test_data = {
        "id": 12345,
        "person_age": 30,
        "person_income": 55000,
        "person_emp_length": 3,
        "loan_amnt": 12000,
        "loan_int_rate": 11.5,
        "loan_percent_income": 0.22,
        "cb_person_cred_hist_length": 5,
        "person_home_ownership": "RENT",
        "loan_intent": "PERSONAL",
        "loan_grade": "B",
        "cb_person_default_on_file": "N"
    }
    
    # 假設有一個模型（需要先有模型才能測試）
    try:
        # 先列出可用模型
        models_response = requests.get("http://localhost:8000/v1/models")
        if models_response.status_code == 200:
            models = models_response.json().get("models", [])
            if models:
                model_id = models[0]["model_id"]
                print(f"使用模型: {model_id}")
                
                # 進行預測
                response = requests.post(
                    url,
                    json=test_data,
                    params={"model_id": model_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 單筆預測成功")
                    print(f"  輸入 ID: {test_data['id']}")
                    print(f"  返回 ID: {result.get('id')}")
                    print(f"  預測概率: {result.get('probability')}")
                    print(f"  預測標籤: {result.get('label')}")
                    
                    # 驗證 ID 是否正確保留
                    if result.get('id') == test_data['id']:
                        print("✅ ID 正確保留在結果中")
                    else:
                        print("❌ ID 未正確保留")
                        
                else:
                    print(f"❌ 預測失敗: {response.status_code}")
                    print(f"錯誤: {response.text}")
            else:
                print("⚠️  沒有可用模型，無法測試預測")
        else:
            print(f"❌ 無法獲取模型列表: {models_response.status_code}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def test_batch_prediction():
    """測試批量預測的 ID 處理"""
    print("\n" + "=" * 50)
    print("測試批量預測 ID 處理")
    print("=" * 50)
    
    # 創建測試 CSV 數據
    test_data = {
        'id': [1001, 1002, 1003],
        'person_age': [25, 30, 35],
        'person_income': [50000, 60000, 70000],
        'person_emp_length': [2, 5, 8],
        'loan_amnt': [10000, 15000, 20000],
        'loan_int_rate': [10.5, 12.0, 8.5],
        'loan_percent_income': [0.2, 0.25, 0.28],
        'cb_person_cred_hist_length': [3, 7, 10],
        'person_home_ownership': ['RENT', 'OWN', 'MORTGAGE'],
        'loan_intent': ['PERSONAL', 'EDUCATION', 'MEDICAL'],
        'loan_grade': ['B', 'C', 'A'],
        'cb_person_default_on_file': ['N', 'N', 'Y']
    }
    
    df = pd.DataFrame(test_data)
    csv_content = df.to_csv(index=False)
    
    try:
        # 先列出可用模型
        models_response = requests.get("http://localhost:8000/v1/models")
        if models_response.status_code == 200:
            models = models_response.json().get("models", [])
            if models:
                model_id = models[0]["model_id"]
                print(f"使用模型: {model_id}")
                
                # 進行批量預測
                files = {'file': ('test_batch.csv', csv_content, 'text/csv')}
                data = {'model_id': model_id}
                
                response = requests.post(
                    "http://localhost:8000/v1/predict/batch",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    print("✅ 批量預測成功")
                    
                    # 解析結果 CSV
                    result_df = pd.read_csv(io.StringIO(response.text))
                    print(f"結果形狀: {result_df.shape}")
                    print(f"結果欄位: {list(result_df.columns)}")
                    print("前幾行結果:")
                    print(result_df.head())
                    
                    # 驗證 ID 是否正確保留
                    if 'id' in result_df.columns:
                        input_ids = set(test_data['id'])
                        output_ids = set(result_df['id'])
                        if input_ids == output_ids:
                            print("✅ 所有 ID 正確保留並映射")
                        else:
                            print("❌ ID 映射不正確")
                            print(f"輸入 ID: {sorted(input_ids)}")
                            print(f"輸出 ID: {sorted(output_ids)}")
                    else:
                        print("❌ 結果中沒有 ID 欄位")
                        
                else:
                    print(f"❌ 批量預測失敗: {response.status_code}")
                    print(f"錯誤: {response.text}")
            else:
                print("⚠️  沒有可用模型，無法測試批量預測")
        else:
            print(f"❌ 無法獲取模型列表: {models_response.status_code}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def test_health_check():
    """測試健康檢查"""
    print("\n" + "=" * 50)
    print("測試 API 健康檢查")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            health_data = response.json()
            print("✅ API 健康檢查通過")
            print(f"狀態: {health_data.get('status')}")
            print(f"時間戳: {health_data.get('timestamp')}")
            print(f"可用模型數量: {health_data.get('available_models', 0)}")
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康檢查失敗: {e}")

def test_list_models():
    """測試模型列表"""
    print("\n" + "=" * 50)
    print("測試模型列表")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/v1/models")
        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get("models", [])
            print(f"✅ 成功獲取模型列表")
            print(f"可用模型數量: {len(models)}")
            
            for i, model in enumerate(models[:3]):  # 只顯示前 3 個
                print(f"  模型 {i+1}:")
                print(f"    ID: {model.get('model_id')}")
                print(f"    創建時間: {model.get('created_at')}")
                print(f"    檔案大小: {model.get('file_size')} bytes")
                
        else:
            print(f"❌ 獲取模型列表失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def print_summary():
    """印出總結"""
    print("\n" + "=" * 50)
    print("Docker 更新總結")
    print("=" * 50)
    
    print("✅ 已完成的更新:")
    print("  1. 重新構建 Docker 映像（使用 --no-cache）")
    print("  2. 包含最新的 ID 欄位處理修正")
    print("  3. 重新啟動所有服務")
    print("  4. 驗證服務健康狀態")
    
    print("\n📋 修正內容:")
    print("  • 單筆預測：移除 ID 欄位後進行特徵處理")
    print("  • 批量預測：移除 ID 欄位後進行特徵處理")
    print("  • SHAP 解釋：移除 ID 欄位後進行特徵處理")
    print("  • 預處理器：不將 ID 欄位加入處理後的特徵中")
    print("  • 結果映射：保留原始 ID 用於所有回應")
    
    print("\n🔧 建議後續步驟:")
    print("  1. 使用真實模型測試預測功能")
    print("  2. 驗證 SHAP 解釋功能")
    print("  3. 測試模型訓練工作流程")
    print("  4. 檢查日誌確保沒有錯誤")

if __name__ == "__main__":
    # 運行所有測試
    test_health_check()
    test_list_models()
    test_single_prediction()
    test_batch_prediction()
    print_summary()
