import requests
import pandas as pd

# 測試數據
test_data = {
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
}

# 創建 DataFrame 並保存為 CSV
df = pd.DataFrame(test_data)
df.to_csv('test_batch_requests.csv', index=False)

# 發送批量預測請求
url = "http://localhost:8000/v1/predict/batch"
files = {'file': open('test_batch_requests.csv', 'rb')}
data = {'model_id': 'model_20250815_204558_dfd4d9c0'}

try:
    response = requests.post(url, files=files, data=data, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("Response Content:")
        print(response.text)
    else:
        print("Error Response:")
        print(response.text)
        
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
finally:
    files['file'].close()
