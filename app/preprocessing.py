"""
數據預處理模組
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import List, Dict, Any, Tuple
import logging
import pickle

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """
    數據預處理類別
    處理數值特徵標準化和類別特徵 One-Hot 編碼
    """
    
    def __init__(self):
        self.numerical_features = [
            'person_age', 'person_income', 'person_emp_length',
            'loan_amnt', 'loan_int_rate', 'loan_percent_income',
            'cb_person_cred_hist_length'
        ]
        
        self.categorical_features = [
            'person_home_ownership', 'loan_intent', 
            'loan_grade', 'cb_person_default_on_file'
        ]
        
        # 固定的類別值映射 (drop first for each category to avoid multicollinearity)
        self.categorical_mappings = {
            'person_home_ownership': ['MORTGAGE', 'OTHER', 'OWN', 'RENT'],  # drop first: skip MORTGAGE
            'loan_intent': ['DEBTCONSOLIDATION', 'EDUCATION', 'HOMEIMPROVEMENT', 'MEDICAL', 'PERSONAL', 'VENTURE'],  # drop first: skip DEBTCONSOLIDATION
            'loan_grade': ['A', 'B', 'C', 'D', 'E', 'F', 'G'],  # drop first: skip A
            'cb_person_default_on_file': ['N', 'Y']  # drop first: skip N
        }
        
        self.target_column = 'loan_status'
        self.scaler = StandardScaler()
        self.feature_names = None
        self.is_fitted = False
        
    def fit(self, df: pd.DataFrame) -> 'DataPreprocessor':
        """
        訓練預處理器（只使用特徵，不依賴目標列）
        
        Args:
            df: 包含特徵的 DataFrame（可以包含或不包含目標列）
            
        Returns:
            訓練好的預處理器
        """
        logger.info("開始訓練數據預處理器...")
        
        # 移除目標列（如果存在）
        features_df = df.drop(columns=[self.target_column], errors='ignore')
        
        # 驗證必要的特徵欄位
        self._validate_columns(features_df, require_target=False)
        
        # 只使用數值特徵訓練標準化器
        X_num = features_df[self.numerical_features]
        self.scaler.fit(X_num)
        
        # 生成固定的特徵名稱
        self._generate_fixed_feature_names()
        
        self.is_fitted = True
        logger.info(f"預處理器訓練完成，總特徵數: {len(self.feature_names)}")
        
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        轉換數據
        
        Args:
            df: 要轉換的 DataFrame
            
        Returns:
            轉換後的 DataFrame
        """
        if not self.is_fitted:
            raise ValueError("預處理器尚未訓練，請先調用 fit() 方法")
        
        # 移除 id 欄位以避免驗證失敗
        if 'id' in df.columns:
            df_for_processing = df.drop('id', axis=1)
        else:
            df_for_processing = df.copy()
        
        # 驗證欄位（不包含 id）
        self._validate_columns(df_for_processing, require_target=False)
        
        # 處理數值特徵
        X_num = df_for_processing[self.numerical_features]
        X_num = self._handle_missing_values_numerical(X_num)
        X_num_scaled = self.scaler.transform(X_num)
        
        # 處理類別特徵
        X_cat = df_for_processing[self.categorical_features]
        X_cat = self._handle_missing_values_categorical(X_cat)
        X_cat_encoded = self._manual_onehot_encode(X_cat)
        
        # 合併特徵
        X_processed = np.concatenate([X_num_scaled, X_cat_encoded], axis=1)
        
        # 轉換為 DataFrame
        X_processed_df = pd.DataFrame(
            X_processed,
            columns=self.feature_names,
            index=df_for_processing.index
        )
        
        return X_processed_df
    
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        訓練並轉換數據（只處理特徵，不處理目標變數）
        
        Args:
            df: 包含特徵的 DataFrame（可以包含或不包含目標列）
            
        Returns:
            轉換後的特徵 DataFrame
        """
        # 如果包含目標列，先移除（但不返回）
        features_df = df.drop(columns=[self.target_column], errors='ignore')
        
        # 訓練和轉換
        self.fit(features_df)
        X_processed = self.transform(features_df)
        
        return X_processed
    
    def fit_transform_with_target(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        訓練並轉換數據，同時分離目標變數（為了向後兼容）
        
        Args:
            df: 包含所有特徵和目標的 DataFrame
            
        Returns:
            轉換後的特徵和目標
        """
        # 分離目標變數
        if self.target_column not in df.columns:
            raise ValueError(f"數據中缺少目標列: {self.target_column}")
            
        y = df[self.target_column]
        X_features = df.drop(columns=[self.target_column])
        
        # 訓練和轉換特徵
        X_processed = self.fit_transform(X_features)
        
        return X_processed, y
    
    def _validate_columns(self, df: pd.DataFrame, require_target: bool = True):
        """
        驗證必要欄位
        
        Args:
            df: 要驗證的 DataFrame
            require_target: 是否需要目標變數
        """
        required_cols = self.numerical_features + self.categorical_features
        if require_target:
            required_cols.append(self.target_column)
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"缺少必要欄位: {missing_cols}")
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        處理缺失值
        
        Args:
            df: 包含缺失值的 DataFrame
            
        Returns:
            處理後的 DataFrame
        """
        df_clean = df.copy()
        
        # 數值型特徵：用中位數填補
        for col in self.numerical_features:
            if col in df_clean.columns and df_clean[col].isnull().any():
                median_val = df_clean[col].median()
                df_clean[col].fillna(median_val, inplace=True)
                logger.info(f"欄位 {col} 缺失值已用中位數 {median_val} 填補")
        
        # 類別型特徵：用眾數填補
        for col in self.categorical_features:
            if col in df_clean.columns and df_clean[col].isnull().any():
                mode_val = df_clean[col].mode()[0] if not df_clean[col].mode().empty else 'Unknown'
                df_clean[col].fillna(mode_val, inplace=True)
                logger.info(f"欄位 {col} 缺失值已用眾數 {mode_val} 填補")
        
        return df_clean
    
    def _generate_fixed_feature_names(self):
        """
        生成固定的特徵名稱
        """
        feature_names = []
        
        # 數值特徵名稱
        feature_names.extend(self.numerical_features)
        
        # 固定的 One-Hot 編碼特徵名稱 (drop first)
        for col, categories in self.categorical_mappings.items():
            # 跳過第一個類別以避免多重共線性
            for cat in categories[1:]:
                feature_names.append(f"{col}_{cat}")
        
        self.feature_names = feature_names
    
    def _manual_onehot_encode(self, X_cat: pd.DataFrame) -> np.ndarray:
        """
        手動 One-Hot 編碼
        
        Args:
            X_cat: 類別特徵 DataFrame
            
        Returns:
            編碼後的 numpy 數組
        """
        encoded_features = []
        
        for col in self.categorical_features:
            col_data = X_cat[col]
            categories = self.categorical_mappings[col]
            
            # 為每個類別創建 dummy 變數（跳過第一個類別）
            for cat in categories[1:]:
                encoded_col = (col_data == cat).astype(int)
                encoded_features.append(encoded_col.values)
        
        # 堆疊所有編碼特徵
        if encoded_features:
            return np.column_stack(encoded_features)
        else:
            return np.empty((len(X_cat), 0))
    
    def _handle_missing_values_numerical(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        處理數值特徵的缺失值
        
        Args:
            df: 數值特徵 DataFrame
            
        Returns:
            處理後的 DataFrame
        """
        df_clean = df.copy()
        
        for col in self.numerical_features:
            if col in df_clean.columns and df_clean[col].isnull().any():
                median_val = df_clean[col].median()
                df_clean[col].fillna(median_val, inplace=True)
                logger.info(f"欄位 {col} 缺失值已用中位數 {median_val} 填補")
        
        return df_clean
    
    def _handle_missing_values_categorical(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        處理類別特徵的缺失值
        
        Args:
            df: 類別特徵 DataFrame
            
        Returns:
            處理後的 DataFrame
        """
        df_clean = df.copy()
        
        for col in self.categorical_features:
            if col in df_clean.columns and df_clean[col].isnull().any():
                # 用第一個類別（最常見的）填補
                mode_val = self.categorical_mappings[col][0]
                df_clean[col].fillna(mode_val, inplace=True)
                logger.info(f"欄位 {col} 缺失值已用模式 {mode_val} 填補")
        
        return df_clean
    
    def get_feature_names(self) -> List[str]:
        """
        獲取特徵名稱列表
        
        Returns:
            特徵名稱列表
        """
        if not self.is_fitted:
            raise ValueError("預處理器尚未訓練")
        return self.feature_names
    
    def get_feature_info(self) -> Dict[str, Any]:
        """
        獲取特徵資訊
        
        Returns:
            特徵資訊字典
        """
        if not self.is_fitted:
            raise ValueError("預處理器尚未訓練")
        
        return {
            'total_features': len(self.feature_names),
            'numerical_features': len(self.numerical_features),
            'categorical_features': len(self.categorical_features),
            'feature_names': self.feature_names,
            'numerical_feature_names': self.numerical_features,
            'categorical_feature_names': self.categorical_features
        }
    
    def save_preprocessor(self, filepath: str):
        """
        保存預處理器
        
        Args:
            filepath: 保存路徑
        """
        preprocessor_data = {
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'numerical_features': self.numerical_features,
            'categorical_features': self.categorical_features,
            'categorical_mappings': self.categorical_mappings,
            'target_column': self.target_column,
            'is_fitted': self.is_fitted
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(preprocessor_data, f)
        
        logger.info(f"預處理器已保存至: {filepath}")
    
    @classmethod
    def load_preprocessor(cls, filepath: str) -> 'DataPreprocessor':
        """
        載入預處理器
        
        Args:
            filepath: 預處理器路徑
            
        Returns:
            載入的預處理器
        """
        with open(filepath, 'rb') as f:
            preprocessor_data = pickle.load(f)
        
        # 創建新實例
        preprocessor = cls()
        
        # 恢復狀態
        preprocessor.scaler = preprocessor_data['scaler']
        preprocessor.feature_names = preprocessor_data['feature_names']
        preprocessor.numerical_features = preprocessor_data[
            'numerical_features'
        ]
        preprocessor.categorical_features = preprocessor_data[
            'categorical_features'
        ]
        preprocessor.categorical_mappings = preprocessor_data.get(
            'categorical_mappings', preprocessor.categorical_mappings
        )
        preprocessor.target_column = preprocessor_data['target_column']
        preprocessor.is_fitted = preprocessor_data['is_fitted']
        
        logger.info(f"預處理器已從 {filepath} 載入")
        return preprocessor

class AdvancedDataPreprocessor(DataPreprocessor):
    """
    進階數據預處理類別
    包含特徵工程功能
    """
    
    def __init__(self, create_interactions: bool = True):
        super().__init__()
        self.create_interactions = create_interactions
    
    def fit(self, df: pd.DataFrame) -> 'AdvancedDataPreprocessor':
        """
        訓練進階預處理器
        
        Args:
            df: 包含所有特徵的 DataFrame
            
        Returns:
            訓練好的預處理器
        """
        logger.info("開始訓練進階數據預處理器...")
        
        # 移除目標列和 id 字段
        df_for_training = df.copy()
        if 'id' in df_for_training.columns:
            df_for_training = df_for_training.drop('id', axis=1)
        if self.target_column in df_for_training.columns:
            df_for_training = df_for_training.drop(self.target_column, axis=1)
        
        # 創建交互特徵
        if self.create_interactions:
            df_for_training = self._create_interaction_features(
                df_for_training
            )
        
        # 更新特徵列表以包含新的交互特徵
        self._update_feature_lists(df_for_training)
        
        # 驗證必要的特徵欄位（不包含目標列）
        self._validate_columns(df_for_training, require_target=False)
        
        # 只使用數值特徵訓練標準化器
        X_num = df_for_training[self.numerical_features]
        self.scaler.fit(X_num)
        
        # 生成固定的特徵名稱
        self._generate_fixed_feature_names()
        
        self.is_fitted = True
        logger.info(f"進階預處理器訓練完成，總特徵數: {len(self.feature_names)}")
        
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        轉換數據（包含特徵工程）
        
        Args:
            df: 要轉換的 DataFrame
            
        Returns:
            轉換後的 DataFrame
        """
        if not self.is_fitted:
            raise ValueError("預處理器尚未訓練，請先調用 fit() 方法")
        
        # 移除 id 欄位（如果存在）
        if 'id' in df.columns:
            df = df.drop('id', axis=1)
        
        # 創建交互特徵
        if self.create_interactions:
            df = self._create_interaction_features(df)
        
        # 移除目標列（如果存在）
        if self.target_column in df.columns:
            df = df.drop(columns=[self.target_column], errors='ignore')
        
        # 驗證欄位（不包含 id）
        self._validate_columns(df, require_target=False)
        
        # 處理數值特徵
        X_num = df[self.numerical_features]
        X_num = self._handle_missing_values_numerical(X_num)
        X_num_scaled = self.scaler.transform(X_num)
        
        # 處理類別特徵
        X_cat = df[self.categorical_features]
        X_cat = self._handle_missing_values_categorical(X_cat)
        X_cat_encoded = self._manual_onehot_encode(X_cat)
        
        # 合併特徵
        X_processed = np.concatenate([X_num_scaled, X_cat_encoded], axis=1)
        
        # 轉換為 DataFrame
        X_processed_df = pd.DataFrame(
            X_processed,
            columns=self.feature_names,
            index=df.index
        )
        
        # 注意：不要重新加入 id 欄位到特徵矩陣中
        # id 欄位應該在 API 層面處理，不應該成為特徵的一部分
        
        return X_processed_df
    
    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        創建交互特徵
        
        Args:
            df: 輸入 DataFrame
            
        Returns:
            包含交互特徵的 DataFrame
        """
        df_enhanced = df.copy()
        
        # 收入相關交互特徵
        if all(col in df.columns for col in ['person_income', 'loan_amnt']):
            df_enhanced['income_to_loan_ratio'] = (
                df_enhanced['person_income'] / (df_enhanced['loan_amnt'] + 1)
            )
        
        if all(col in df.columns for col in ['person_income', 'person_age']):
            df_enhanced['income_per_age'] = (
                df_enhanced['person_income'] / (df_enhanced['person_age'] + 1)
            )
        
        # 年齡相關交互特徵
        if all(col in df.columns for col in ['person_age', 'person_emp_length']):
            df_enhanced['age_emp_ratio'] = (
                df_enhanced['person_age'] / (df_enhanced['person_emp_length'] + 1)
            )
        
        # 貸款相關交互特徵
        if all(col in df.columns for col in ['loan_amnt', 'loan_int_rate']):
            df_enhanced['loan_cost'] = (
                df_enhanced['loan_amnt'] * df_enhanced['loan_int_rate'] / 100
            )
        
        # 信用相關特徵
        if all(col in df.columns for col in ['cb_person_cred_hist_length', 'person_age']):
            df_enhanced['credit_history_ratio'] = (
                df_enhanced['cb_person_cred_hist_length'] / (df_enhanced['person_age'] + 1)
            )
        
        # 風險評分特徵
        if all(col in df.columns for col in ['loan_percent_income', 'loan_int_rate']):
            df_enhanced['risk_score'] = (
                df_enhanced['loan_percent_income'] * df_enhanced['loan_int_rate']
            )
        
        logger.info(f"創建了 {df_enhanced.shape[1] - df.shape[1]} 個交互特徵")
        return df_enhanced
    
    def _update_feature_lists(self, df: pd.DataFrame):
        """
        更新特徵列表以包含新創建的特徵（只在第一次訓練時更新）
        
        Args:
            df: 包含所有特徵的 DataFrame
        """
        # 只有在首次訓練且未設置時才更新特徵列表
        if not hasattr(self, '_features_updated') or not self._features_updated:
            # 找出新創建的數值特徵
            all_numerical = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # 移除目標變數和 id 欄位
            if self.target_column in all_numerical:
                all_numerical.remove(self.target_column)
            if 'id' in all_numerical:
                all_numerical.remove('id')
            
            # 更新數值特徵列表
            self.numerical_features = all_numerical
            self._features_updated = True
            
            logger.info(f"更新後的數值特徵數量: {len(self.numerical_features)}")
            logger.info(f"類別特徵數量: {len(self.categorical_features)}")
        else:
            logger.info(f"使用已確定的特徵列表 - 數值: {len(self.numerical_features)}, 類別: {len(self.categorical_features)}")
