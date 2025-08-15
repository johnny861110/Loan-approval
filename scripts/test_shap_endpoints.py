#!/usr/bin/env python3
"""
測試 SHAP 相關 API 端點
"""

import requests
import json
import pandas as pd
import sys

# API 基礎 URL
BASE_URL = 'http://localhost:8001'
MODEL_ID = 'model_20250815_225226_4f9b4198'

def test_global_shap():
    """測試全域 SHAP"""
    print('📊 測試全域 SHAP 特徵重要性...')
    try:
        response = requests.get(f'{BASE_URL}/v1/shap/global?model_id={MODEL_ID}')
        print(f'狀態碼: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print('✅ 全域 SHAP 成功')
            print(f'模型 ID: {data["model_id"]}')
            print(f'特徵重要性數量: {len(data["feature_importance"])}')
            print('前 5 個重要特徵:')
            for i, (feature, importance) in enumerate(data['feature_importance'][:5]):
                print(f'  {i+1}. {feature}: {importance:.4f}')
            return True
        else:
            print(f'❌ 全域 SHAP 失敗: {response.text}')
            return False
    except Exception as e:
        print(f'❌ 全域 SHAP 錯誤: {e}')
        return False

def test_local_shap():
    """測試單筆 SHAP"""
    print('🎯 測試單筆 SHAP 解釋...')
    try:
        test_data = {
            'id': 1,
            'person_age': 25,
            'person_income': 50000,
            'person_home_ownership': 'RENT',
            'person_emp_length': 2.0,
            'loan_intent': 'PERSONAL',
            'loan_grade': 'B',
            'loan_amnt': 10000,
            'loan_int_rate': 12.5,
            'loan_percent_income': 0.2,
            'cb_person_default_on_file': 'N',
            'cb_person_cred_hist_length': 3
        }
        
        response = requests.post(
            f'{BASE_URL}/v1/shap/local?model_id={MODEL_ID}',
            json=test_data
        )
        print(f'狀態碼: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print('✅ 單筆 SHAP 成功')
            print(f'ID: {data["id"]}')
            print(f'模型 ID: {data["model_id"]}')
            print(f'基準值: {data["base_value"]:.4f}')
            print(f'SHAP 值數量: {len(data["shap_values"])}')
            
            # 顯示前 5 個 SHAP 值
            print('前 5 個特徵的 SHAP 值:')
            for i in range(min(5, len(data['features']))):
                feature = data['features'][i]
                shap_val = data['shap_values'][i]
                print(f'  {feature}: {shap_val:.4f}')
            return True
        else:
            print(f'❌ 單筆 SHAP 失敗: {response.text}')
            return False
    except Exception as e:
        print(f'❌ 單筆 SHAP 錯誤: {e}')
        return False

def test_batch_shap():
    """測試批量 SHAP"""
    print('📋 測試批量 SHAP 解釋...')
    try:
        # 創建測試檔案
        test_batch_data = pd.DataFrame([
            {
                'id': 1,
                'person_age': 25,
                'person_income': 50000,
                'person_home_ownership': 'RENT',
                'person_emp_length': 2.0,
                'loan_intent': 'PERSONAL',
                'loan_grade': 'B',
                'loan_amnt': 10000,
                'loan_int_rate': 12.5,
                'loan_percent_income': 0.2,
                'cb_person_default_on_file': 'N',
                'cb_person_cred_hist_length': 3
            },
            {
                'id': 2,
                'person_age': 35,
                'person_income': 75000,
                'person_home_ownership': 'OWN',
                'person_emp_length': 8.0,
                'loan_intent': 'EDUCATION',
                'loan_grade': 'A',
                'loan_amnt': 15000,
                'loan_int_rate': 8.5,
                'loan_percent_income': 0.15,
                'cb_person_default_on_file': 'N',
                'cb_person_cred_hist_length': 10
            }
        ])
        
        test_batch_data.to_csv('test_shap_batch.csv', index=False)
        print('✅ 測試檔案已創建: test_shap_batch.csv')
        
        # 發送批量 SHAP 請求
        with open('test_shap_batch.csv', 'rb') as f:
            files = {'file': ('test_shap_batch.csv', f, 'text/csv')}
            data = {'model_id': MODEL_ID}
            
            response = requests.post(
                f'{BASE_URL}/v1/shap/batch',
                files=files,
                data=data
            )
        
        print(f'狀態碼: {response.status_code}')
        
        if response.status_code == 200:
            print('✅ 批量 SHAP 成功')
            
            # 保存結果
            with open('shap_results.csv', 'wb') as f:
                f.write(response.content)
            
            # 讀取並顯示結果
            results_df = pd.read_csv('shap_results.csv')
            print(f'結果形狀: {results_df.shape}')
            print('結果欄位:', list(results_df.columns)[:10])  # 只顯示前 10 個欄位
            print('前 2 行結果:')
            print(results_df.head(2).to_string())
            return True
        else:
            print(f'❌ 批量 SHAP 失敗: {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ 批量 SHAP 錯誤: {e}')
        return False

def main():
    """主測試函數"""
    print('🔍 測試 SHAP 相關 API 端點')
    print('=' * 50)
    
    results = []
    
    # 測試全域 SHAP
    results.append(test_global_shap())
    print()
    
    # 測試單筆 SHAP
    results.append(test_local_shap())
    print()
    
    # 測試批量 SHAP
    results.append(test_batch_shap())
    print()
    
    # 總結
    print('📋 測試總結:')
    test_names = ['全域 SHAP', '單筆 SHAP', '批量 SHAP']
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = '✅' if result else '❌'
        print(f'{name}: {status}')
    
    all_passed = all(results)
    if all_passed:
        print('\n🎉 所有 SHAP 測試通過！')
    else:
        print('\n⚠️ 部分測試失敗')
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
