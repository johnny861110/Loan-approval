"""
詳細的 ID 欄位處理驗證測試
"""

import pandas as pd
import numpy as np
from app.preprocessing import DataPreprocessor


def test_complete_workflow():
    """測試完整的工作流程，確保 ID 欄位不會洩露到模型中"""
    
    print("🔍 詳細的 ID 欄位處理驗證測試")
    print("=" * 60)
    
    # 1. 創建更大的測試數據集
    np.random.seed(42)
    n_samples = 100
    
    test_data = {
        'id': range(1, n_samples + 1),
        'person_age': np.random.randint(18, 80, n_samples),
        'person_income': np.random.randint(20000, 150000, n_samples),
        'person_emp_length': np.random.randint(0, 40, n_samples),
        'loan_amnt': np.random.randint(1000, 50000, n_samples),
        'loan_int_rate': np.random.uniform(5.0, 25.0, n_samples),
        'loan_percent_income': np.random.uniform(0.1, 0.8, n_samples),
        'cb_person_cred_hist_length': np.random.randint(1, 30, n_samples),
        'person_home_ownership': np.random.choice(['RENT', 'OWN', 'MORTGAGE'], n_samples),
        'loan_intent': np.random.choice(['PERSONAL', 'EDUCATION', 'MEDICAL', 'VENTURE'], n_samples),
        'loan_grade': np.random.choice(['A', 'B', 'C', 'D', 'E', 'F', 'G'], n_samples),
        'cb_person_default_on_file': np.random.choice(['Y', 'N'], n_samples),
        'loan_status': np.random.choice([0, 1], n_samples)
    }
    
    df = pd.DataFrame(test_data)
    print(f"📊 測試數據集大小: {df.shape}")
    print(f"📋 原始欄位: {list(df.columns)}")
    
    # 2. 測試訓練流程
    print(f"\n🏋️ 測試訓練流程...")
    preprocessor = DataPreprocessor()
    
    # 分離訓練和測試數據
    train_df = df.iloc[:80].copy()
    test_df = df.iloc[80:].copy()
    
    # 訓練預處理器
    X_train, y_train = preprocessor.fit_transform(train_df)
    
    print(f"✅ 訓練數據處理完成")
    print(f"   - X_train 形狀: {X_train.shape}")
    print(f"   - y_train 形狀: {y_train.shape}")
    print(f"   - X_train 欄位: {list(X_train.columns)}")
    
    # 檢查訓練數據中是否包含 ID
    if 'id' in X_train.columns:
        print("❌ 錯誤：訓練特徵中包含 ID 欄位！")
        return False
    else:
        print("✅ 訓練特徵中不包含 ID 欄位")
    
    # 3. 測試預測流程
    print(f"\n🔮 測試預測流程...")
    
    # 移除目標變數進行預測
    test_features = test_df.drop('loan_status', axis=1)
    print(f"   - 測試特徵原始形狀: {test_features.shape}")
    print(f"   - 測試特徵欄位: {list(test_features.columns)}")
    
    # 轉換測試數據
    X_test = preprocessor.transform(test_features)
    
    print(f"   - X_test 處理後形狀: {X_test.shape}")
    print(f"   - X_test 欄位: {list(X_test.columns)}")
    
    # 檢查測試數據中是否包含 ID
    if 'id' in X_test.columns:
        print("❌ 錯誤：測試特徵中包含 ID 欄位！")
        return False
    else:
        print("✅ 測試特徵中不包含 ID 欄位")
    
    # 4. 驗證特徵一致性
    print(f"\n🔧 驗證特徵一致性...")
    
    if X_train.shape[1] != X_test.shape[1]:
        print(f"❌ 錯誤：訓練和測試特徵數量不一致！")
        print(f"   - 訓練特徵數: {X_train.shape[1]}")
        print(f"   - 測試特徵數: {X_test.shape[1]}")
        return False
    
    if list(X_train.columns) != list(X_test.columns):
        print("❌ 錯誤：訓練和測試特徵名稱不一致！")
        return False
    
    print("✅ 訓練和測試特徵完全一致")
    
    # 5. 模擬 API 調用場景
    print(f"\n🌐 模擬 API 調用場景...")
    
    # 單筆預測場景
    single_record = test_features.iloc[0:1].copy()
    print(f"   - 單筆記錄原始欄位: {list(single_record.columns)}")
    
    # 模擬 API 處理：移除 ID
    single_record_no_id = single_record.drop('id', axis=1)
    X_single = preprocessor.transform(single_record_no_id)
    
    print(f"   - 單筆處理後形狀: {X_single.shape}")
    print(f"   - 單筆處理後欄位: {list(X_single.columns)}")
    
    if 'id' in X_single.columns:
        print("❌ 錯誤：單筆預測特徵中包含 ID 欄位！")
        return False
    else:
        print("✅ 單筆預測特徵中不包含 ID 欄位")
    
    # 6. 最終報告
    print(f"\n📋 最終驗證報告")
    print("=" * 60)
    
    checks = [
        ("訓練數據不包含 ID", 'id' not in X_train.columns),
        ("測試數據不包含 ID", 'id' not in X_test.columns),
        ("單筆數據不包含 ID", 'id' not in X_single.columns),
        ("特徵數量一致", X_train.shape[1] == X_test.shape[1] == X_single.shape[1]),
        ("特徵名稱一致", list(X_train.columns) == list(X_test.columns) == list(X_single.columns)),
        ("所有特徵都是預期的", all(col != 'id' for col in X_train.columns))
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
        if not check_result:
            all_passed = False
    
    print(f"\n🎯 總體結果: {'所有檢查通過！' if all_passed else '存在問題，需要修正！'}")
    
    return all_passed


if __name__ == "__main__":
    success = test_complete_workflow()
    exit(0 if success else 1)
