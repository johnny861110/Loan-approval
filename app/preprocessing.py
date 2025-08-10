"""
數據預處理模組
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
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
        
        self.target_column = 'loan_status'
        self.preprocessor = None
        self.feature_names = None
        self.is_fitted = False
        
    def fit(self, df: pd.DataFrame) -> 'DataPreprocessor':
        """
        訓練預處理器
        
        Args:
            df: 包含所有特徵的 DataFrame
            
        Returns:
            訓練好的預處理器
        """
        logger.info("開始訓練數據預處理器...")
        
        # 驗證必要欄位
        self._validate_columns(df)
        
        # 分離特徵和目標
        X = df[self.numerical_features + self.categorical_features]
        
        # 創建預處理管道
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), self.numerical_features),
                ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), 
                 self.categorical_features)
            ],
            remainder='passthrough'
        )
        
        # 訓練預處理器
        self.preprocessor.fit(X)
        
        # 生成特徵名稱
        self._generate_feature_names()
        
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
        
        # 保存 id 欄位（如果存在）
        id_column = None
        if 'id' in df.columns:
            id_column = df['id'].copy()
            # 臨時移除 id 欄位以避免驗證失敗
            df_for_processing = df.drop('id', axis=1)
        else:
            df_for_processing = df.copy()
        
        # 驗證欄位（不包含 id）
        self._validate_columns(df_for_processing, require_target=False)
        
        # 分離特徵
        X = df_for_processing[self.numerical_features + self.categorical_features]
        
        # 處理缺失值
        X = self._handle_missing_values(X)
        
        # 應用預處理
        X_processed = self.preprocessor.transform(X)
        
        # 轉換為 DataFrame
        X_processed_df = pd.DataFrame(
            X_processed, 
            columns=self.feature_names,
            index=df_for_processing.index
        )
        
        # 如果原來有 id 欄位，重新加入（但不參與特徵處理）
        if id_column is not None:
            X_processed_df['id'] = id_column
        
        return X_processed_df
    
    def fit_transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        訓練並轉換數據
        
        Args:
            df: 包含所有特徵和目標的 DataFrame
            
        Returns:
            轉換後的特徵和目標
        """
        # 分離目標變數
        y = df[self.target_column]
        
        # 訓練和轉換
        self.fit(df)
        X_processed = self.transform(df)
        
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
    
    def _generate_feature_names(self):
        """
        生成處理後的特徵名稱
        """
        feature_names = []
        
        # 數值特徵名稱
        feature_names.extend(self.numerical_features)
        
        # One-Hot 編碼特徵名稱
        if hasattr(self.preprocessor.named_transformers_['cat'], 'get_feature_names_out'):
            cat_feature_names = self.preprocessor.named_transformers_['cat'].get_feature_names_out(
                self.categorical_features
            )
            feature_names.extend(cat_feature_names)
        else:
            # 手動生成類別特徵名稱 (舊版本 sklearn)
            onehot_encoder = self.preprocessor.named_transformers_['cat']
            for i, col in enumerate(self.categorical_features):
                categories = onehot_encoder.categories_[i][1:]  # drop first
                for cat in categories:
                    feature_names.append(f"{col}_{cat}")
        
        self.feature_names = feature_names
    
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
            'preprocessor': self.preprocessor,
            'feature_names': self.feature_names,
            'numerical_features': self.numerical_features,
            'categorical_features': self.categorical_features,
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
        preprocessor.preprocessor = preprocessor_data['preprocessor']
        preprocessor.feature_names = preprocessor_data['feature_names']
        preprocessor.numerical_features = preprocessor_data['numerical_features']
        preprocessor.categorical_features = preprocessor_data['categorical_features']
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
        
        # 創建交互特徵
        if self.create_interactions:
            df = self._create_interaction_features(df)
        
        # 先更新特徵列表以排除 id 字段
        self._update_feature_lists(df)
        
        # 然後驗證必要欄位（已排除 id）
        self._validate_columns(df)
        
        # 移除 id 字段後再調用父類的 fit 方法
        df_for_training = df.copy()
        if 'id' in df_for_training.columns:
            df_for_training = df_for_training.drop('id', axis=1)
        
        # 調用父類的 fit 方法（不包含 id 字段）
        super().fit(df_for_training)
        
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
        
        # 保存 id 欄位（如果存在）
        id_column = None
        if 'id' in df.columns:
            id_column = df['id'].copy()
            df = df.drop('id', axis=1)
        
        # 創建交互特徵
        if self.create_interactions:
            df = self._create_interaction_features(df)
        
        # 調用父類的 transform 方法
        result = super().transform(df)
        
        # 如果原來有 id 欄位，重新加入（但不參與特徵處理）
        if id_column is not None:
            result['id'] = id_column
        
        return result
    
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
        更新特徵列表以包含新創建的特徵
        
        Args:
            df: 包含所有特徵的 DataFrame
        """
        # 找出新創建的數值特徵
        all_numerical = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # 移除目標變數和 id 欄位
        if self.target_column in all_numerical:
            all_numerical.remove(self.target_column)
        if 'id' in all_numerical:
            all_numerical.remove('id')
        
        # 更新數值特徵列表
        self.numerical_features = all_numerical
        
        logger.info(f"更新後的數值特徵數量: {len(self.numerical_features)}")
        logger.info(f"類別特徵數量: {len(self.categorical_features)}")
