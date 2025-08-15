#!/usr/bin/env python3
"""
使用完整訓練數據訓練新模型，並固定編碼器
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from app.preprocessing import AdvancedDataPreprocessor
from app.model import StackingModel
from app.utils import save_model, generate_model_id
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_fixed_encoder_model():
    """使用完整數據訓練模型，並固定編碼器"""
    
    print("🚀 開始訓練固定編碼器模型...")
    
    # 1. 讀取完整訓練數據
    print("📖 讀取訓練數據...")
    data_path = "data/raw/train.csv"
    df = pd.read_csv(data_path)
    
    print(f"數據形狀: {df.shape}")
    print(f"欄位: {list(df.columns)}")
    
    # 檢查數據
    print("\n數據概覽:")
    print(df.head())
    
    print("\n數據類型:")
    print(df.dtypes)
    
    print("\n缺失值:")
    print(df.isnull().sum())
    
    # 2. 準備數據
    print("\n🔧 準備數據...")
    
    # 分離特徵和目標
    X = df.drop(['loan_status'], axis=1)  # 包含 id
    y = df['loan_status']
    
    print(f"特徵數據形狀: {X.shape}")
    print(f"目標數據形狀: {y.shape}")
    print(f"類別分布: {y.value_counts().to_dict()}")
    
    # 3. 創建和訓練預處理器
    print("\n🛠️ 創建進階預處理器...")
    preprocessor = AdvancedDataPreprocessor(create_interactions=True)
    
    # 使用完整數據擬合預處理器（包含所有可能的類別值）
    print("🎯 擬合預處理器到完整數據集...")
    X_processed = preprocessor.fit_transform(X)
    
    print(f"預處理後特徵數量: {X_processed.shape[1]}")
    print("預處理後特徵列表:")
    feature_names = preprocessor.get_feature_names()
    for i, feature in enumerate(feature_names):
        print(f"  {i+1:2d}. {feature}")
    
    # 4. 分割數據
    print("\n✂️ 分割訓練和測試數據...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, 
        test_size=0.2, 
        random_state=42, 
        stratify=y
    )
    
    print(f"訓練集形狀: {X_train.shape}")
    print(f"測試集形狀: {X_test.shape}")
    
    # 5. 訓練模型
    print("\n🤖 訓練 Stacking 模型...")
    model = StackingModel(
        cv_folds=5,
        random_state=42
    )
    
    # 訓練模型
    model.fit(X_train, y_train)
    
    # 6. 模型評估
    print("\n📊 評估模型...")
    from sklearn.metrics import roc_auc_score, accuracy_score
    
    # 預測訓練集
    train_proba = model.predict_proba(X_train)  # 已經是正類概率
    train_pred = model.predict(X_train)
    train_auc = roc_auc_score(y_train, train_proba)
    train_acc = accuracy_score(y_train, train_pred)
    
    # 預測測試集
    test_proba = model.predict_proba(X_test)  # 已經是正類概率
    test_pred = model.predict(X_test)
    test_auc = roc_auc_score(y_test, test_proba)
    test_acc = accuracy_score(y_test, test_pred)
    
    print(f"訓練集 AUC: {train_auc:.4f}, 準確率: {train_acc:.4f}")
    print(f"測試集 AUC: {test_auc:.4f}, 準確率: {test_acc:.4f}")
    
    # 7. 保存模型
    print("\n💾 保存模型...")
    model_id = generate_model_id()
    model_path = save_model(model, preprocessor, model_id)
    
    print(f"✅ 模型已保存: {model_id}")
    print(f"模型路徑: {model_path}")
    print(f"特徵數量: {len(feature_names)}")
    
    # 8. 驗證保存的模型
    print("\n🔍 驗證保存的模型...")
    from app.utils import load_model
    
    loaded_model_data = load_model(model_id)
    loaded_preprocessor = loaded_model_data['preprocessor']
    loaded_features = loaded_preprocessor.get_feature_names()
    
    print(f"載入的模型特徵數量: {len(loaded_features)}")
    
    if len(loaded_features) == len(feature_names):
        print("✅ 特徵數量匹配！")
    else:
        print(f"❌ 特徵數量不匹配: 預期 {len(feature_names)}, 實際 {len(loaded_features)}")
    
    # 9. 測試預測
    print("\n🧪 測試預測功能...")
    
    # 創建測試樣本
    test_sample = {
        "id": 999999,
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
    
    test_df = pd.DataFrame([test_sample])
    print(f"測試樣本: {test_df.shape}")
    
    # 使用載入的預處理器處理
    test_processed = loaded_preprocessor.transform(test_df)
    print(f"處理後測試樣本: {test_processed.shape}")
    
    # 進行預測
    loaded_model = loaded_model_data['model']
    prediction = loaded_model.predict_proba(test_processed)
    
    print(f"預測概率: {prediction[0]}")
    print(f"預測類別: {loaded_model.predict(test_processed)[0]}")
    
    print(f"\n🎉 訓練完成！新模型 ID: {model_id}")
    
    return model_id, model_path

if __name__ == "__main__":
    model_id, model_path = train_fixed_encoder_model()
