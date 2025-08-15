"""
Stacking 模型 - LightGBM + XGBoost + Logistic Meta Model
優化版本：支持 GPU 加速、改進的進度條、更好的錯誤處理
"""

import numpy as np
import pandas as pd
import warnings
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import lightgbm as lgb
import xgboost as xgb
import shap
import pickle
import logging
from typing import Tuple, List, Dict, Any
from tqdm import tqdm
import sys

# 抑制警告
warnings.filterwarnings("ignore", category=UserWarning, module="lightgbm")
warnings.filterwarnings("ignore", category=UserWarning, module="xgboost")

logger = logging.getLogger(__name__)

class StackingModel:
    """
    LightGBM + XGBoost Stacking 模型
    使用 Logistic Regression 作為 Meta Model
    """
    
    def __init__(self, cv_folds: int = 5, random_state: int = 42):
        self.cv_folds = cv_folds
        self.random_state = random_state
        
        # Base Models - 添加 GPU 支持檢測
        self.lgb_params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.1,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': random_state,
            'class_weight': 'balanced',
            'device_type': 'cpu',  # 可以改為 'gpu' 如果有 GPU
            'force_row_wise': True,  # 避免警告
            'num_threads': -1
        }
        
        self.xgb_params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.9,
            'random_state': random_state,
            'verbosity': 0,
            'scale_pos_weight': 1,  # 可根據數據不平衡調整
            'tree_method': 'hist',  # 可以改為 'gpu_hist' 如果有 GPU
            'n_jobs': -1,
            'use_label_encoder': False
        }
        
        # Meta Model
        self.meta_model = LogisticRegression(random_state=random_state)
        
        # 存儲訓練好的模型
        self.base_models = {'lgb': [], 'xgb': []}
        self.is_fitted = False
        
        # 存儲交叉驗證分數
        self.cv_scores = {}
        
        # SHAP 解釋器
        self.shap_explainer = None
        self.global_shap_values = None
        
    def update_hyperparameters(self, optimized_params: Dict[str, Any]):
        """
        更新超參數（來自 HyperOpt 優化結果）
        
        Args:
            optimized_params: HyperOpt 優化後的參數字典
        """
        logger.info("正在更新模型超參數...")
        
        # 更新 LightGBM 參數
        lgb_updates = {}
        for key, value in optimized_params.items():
            if key.startswith('lgbm_'):
                param_name = key.replace('lgbm_', '')
                lgb_updates[param_name] = value
        
        if lgb_updates:
            self.lgb_params.update(lgb_updates)
            logger.info(f"LightGBM 參數已更新: {lgb_updates}")
        
        # 更新 XGBoost 參數
        xgb_updates = {}
        for key, value in optimized_params.items():
            if key.startswith('xgb_'):
                param_name = key.replace('xgb_', '')
                xgb_updates[param_name] = value
        
        if xgb_updates:
            self.xgb_params.update(xgb_updates)
            logger.info(f"XGBoost 參數已更新: {xgb_updates}")
        
        # 更新 Meta Model 參數
        if 'meta_C' in optimized_params:
            self.meta_model = LogisticRegression(
                C=optimized_params['meta_C'],
                solver=optimized_params.get('meta_solver', 'lbfgs'),
                random_state=self.random_state,
                max_iter=1000
            )
            logger.info(f"Meta Model 參數已更新: C={optimized_params['meta_C']}")
        
        return self
        
    def _train_base_models(self, X: pd.DataFrame, y: pd.Series) -> np.ndarray:
        """
        訓練 Base Models 並產生 Out-of-Fold 預測
        
        Args:
            X: 特徵數據
            y: 目標變數
            
        Returns:
            Out-of-fold 預測結果 (n_samples, n_base_models)
        """
        n_samples = len(X)
        oof_predictions = np.zeros((n_samples, 2))  # LightGBM + XGBoost
        
        # 設定交叉驗證
        skf = StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=self.random_state)
        
        logger.info(f"開始 {self.cv_folds}-Fold 交叉驗證訓練")
        
        # 創建進度條
        fold_pbar = tqdm(
            enumerate(skf.split(X, y)), 
            total=self.cv_folds,
            desc="🔄 交叉驗證進度",
            unit="折",
            ncols=100,
            file=sys.stdout
        )
        
        for fold, (train_idx, val_idx) in fold_pbar:
            fold_pbar.set_description(f"🔄 訓練第 {fold + 1}/{self.cv_folds} 折")
            logger.info(f"訓練第 {fold + 1} 折...")
            
            X_train_fold, X_val_fold = X.iloc[train_idx], X.iloc[val_idx]
            y_train_fold, y_val_fold = y.iloc[train_idx], y.iloc[val_idx]
            
            # 訓練 LightGBM
            fold_pbar.set_postfix_str("📊 訓練 LightGBM...")
            lgb_train = lgb.Dataset(X_train_fold, y_train_fold)
            lgb_val = lgb.Dataset(X_val_fold, y_val_fold, reference=lgb_train)
            
            lgb_model = lgb.train(
                self.lgb_params,
                lgb_train,
                num_boost_round=100,
                valid_sets=[lgb_val],
                callbacks=[lgb.early_stopping(stopping_rounds=10), lgb.log_evaluation(0)]
            )
            
            # LightGBM 預測
            lgb_val_pred = lgb_model.predict(X_val_fold, num_iteration=lgb_model.best_iteration)
            oof_predictions[val_idx, 0] = lgb_val_pred
            
            # 保存 LightGBM 模型
            self.base_models['lgb'].append(lgb_model)
            
            # 訓練 XGBoost
            fold_pbar.set_postfix_str("⚡ 訓練 XGBoost...")
            xgb_init_params = dict(self.xgb_params)
            
            # 使用 XGBoost 低層級 API 以支援 early stopping
            dtrain = xgb.DMatrix(X_train_fold, label=y_train_fold)
            dval = xgb.DMatrix(X_val_fold, label=y_val_fold)
            
            # 設置 XGBoost 訓練參數
            params = {
                'objective': 'binary:logistic',
                'eval_metric': 'logloss',
                'max_depth': self.xgb_params.get('max_depth', 6),
                'learning_rate': self.xgb_params.get('learning_rate', 0.1),
                'subsample': self.xgb_params.get('subsample', 0.8),
                'colsample_bytree': self.xgb_params.get('colsample_bytree', 0.9),
                'random_state': self.xgb_params.get('random_state', 42),
                'verbosity': 0,
                'scale_pos_weight': self.xgb_params.get('scale_pos_weight', 1)
            }
            
            # 直接使用 XGBClassifier 進行訓練
            xgb_model = xgb.XGBClassifier(**xgb_init_params)
            
            # 標準 fit 方法，使用 eval_set 進行早期停止
            xgb_model.fit(
                X_train_fold, y_train_fold,
                eval_set=[(X_val_fold, y_val_fold)],
                verbose=False
            )
            
            
            # XGBoost 預測
            xgb_val_pred = xgb_model.predict_proba(X_val_fold)[:, 1]
            oof_predictions[val_idx, 1] = xgb_val_pred
            
            # 保存 XGBoost 模型
            self.base_models['xgb'].append(xgb_model)
            
            # 計算 Fold 性能
            fold_pred = (lgb_val_pred + xgb_val_pred) / 2
            fold_auc = roc_auc_score(y_val_fold, fold_pred)
            lgb_auc = roc_auc_score(y_val_fold, lgb_val_pred)
            xgb_auc = roc_auc_score(y_val_fold, xgb_val_pred)
            logger.info(f"第 {fold + 1} 折 AUC: {fold_auc:.4f}")
            
            fold_pbar.set_postfix_str(f"✅ LGB: {lgb_auc:.3f}, XGB: {xgb_auc:.3f}, 平均: {fold_auc:.3f}")
        
        fold_pbar.close()
        return oof_predictions
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'StackingModel':
        """
        訓練 Stacking 模型
        
        Args:
            X: 特徵數據
            y: 目標變數
            
        Returns:
            訓練好的模型
        """
        logger.info("開始訓練 Stacking 模型...")
        
        # 創建總體進度條
        total_steps = 4  # Base Models + Meta Model + Performance + SHAP
        main_pbar = tqdm(
            total=total_steps,
            desc="🚀 Stacking 模型訓練",
            unit="步驟",
            ncols=100,
            file=sys.stdout
        )
        
        try:
            # 步驟 1: 訓練 Base Models
            main_pbar.set_description("🔄 訓練 Base Models")
            oof_predictions = self._train_base_models(X, y)
            main_pbar.update(1)
            
            # 步驟 2: 訓練 Meta Model
            main_pbar.set_description("🧠 訓練 Meta Model")
            logger.info("訓練 Meta Model (Logistic Regression)...")
            self.meta_model.fit(oof_predictions, y)
            main_pbar.update(1)
            
            # 步驟 3: 計算整體性能
            main_pbar.set_description("📊 計算模型性能")
            meta_pred = self.meta_model.predict_proba(oof_predictions)[:, 1]
            overall_auc = roc_auc_score(y, meta_pred)
            overall_acc = accuracy_score(y, (meta_pred >= 0.5).astype(int))
            
            # 存儲 CV 分數
            self.cv_scores = {
                'mean_auc': float(overall_auc),
                'mean_accuracy': float(overall_acc),
                'cv_folds': self.cv_folds,
                'total_samples': len(X),
                'features_count': X.shape[1]
            }
            
            logger.info(f"Stacking 模型訓練完成!")
            logger.info(f"整體 AUC: {overall_auc:.4f}")
            logger.info(f"整體準確率: {overall_acc:.4f}")
            main_pbar.update(1)
            
            # 步驟 4: 計算 SHAP 值
            main_pbar.set_description("🔍 計算 SHAP 值")
            self._compute_shap_values(X, y)
            main_pbar.update(1)
            
            main_pbar.set_description("✅ 訓練完成")
            main_pbar.close()
            
        except Exception as e:
            main_pbar.close()
            raise e
        
        self.is_fitted = True
        return self
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        預測機率
        
        Args:
            X: 特徵數據
            
        Returns:
            預測機率
        """
        if not self.is_fitted:
            raise ValueError("模型尚未訓練，請先調用 fit() 方法")
        
        # Base Models 預測
        base_predictions = self._get_base_predictions(X)
        
        # Meta Model 預測
        final_pred = self.meta_model.predict_proba(base_predictions)[:, 1]
        
        return final_pred
    
    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """
        預測類別
        
        Args:
            X: 特徵數據
            threshold: 分類閾值
            
        Returns:
            預測類別
        """
        probas = self.predict_proba(X)
        return (probas >= threshold).astype(int)
    
    def _get_base_predictions(self, X: pd.DataFrame) -> np.ndarray:
        """
        獲得 Base Models 的平均預測
        
        Args:
            X: 特徵數據
            
        Returns:
            Base Models 預測結果
        """
        n_samples = len(X)
        base_predictions = np.zeros((n_samples, 2))
        
        # LightGBM 預測 (多個 fold 的平均)
        lgb_preds = []
        for lgb_model in self.base_models['lgb']:
            lgb_pred = lgb_model.predict(X, num_iteration=lgb_model.best_iteration)
            lgb_preds.append(lgb_pred)
        base_predictions[:, 0] = np.mean(lgb_preds, axis=0)
        
        # XGBoost 預測 (多個 fold 的平均)
        xgb_preds = []
        for xgb_model in self.base_models['xgb']:
            # 使用標準的 XGBClassifier predict_proba
            xgb_pred = xgb_model.predict_proba(X)[:, 1]
            xgb_preds.append(xgb_pred)
        base_predictions[:, 1] = np.mean(xgb_preds, axis=0)
        
        return base_predictions
    
    def _compute_shap_values(self, X: pd.DataFrame, y: pd.Series):
        """
        計算 SHAP 值用於模型解釋
        
        Args:
            X: 特徵數據
            y: 目標變數
        """
        try:
            logger.info("計算 SHAP 值...")
            
            # 創建 SHAP 計算進度條
            shap_pbar = tqdm(
                total=3,
                desc="🔍 SHAP 解釋計算",
                unit="步驟",
                ncols=100,
                file=sys.stdout
            )
            
            # 步驟 1: 建立 SHAP 解釋器
            shap_pbar.set_description("🔧 建立 SHAP 解釋器")
            if self.base_models['xgb']:
                model_for_shap = self.base_models['xgb'][0]
                self.shap_explainer = shap.TreeExplainer(model_for_shap)
                shap_pbar.update(1)
                
                # 步驟 2: 準備樣本數據
                shap_pbar.set_description("📊 準備樣本數據")
                sample_size = min(1000, len(X))
                X_sample = X.sample(n=sample_size, random_state=self.random_state)
                shap_pbar.update(1)
                
                # 步驟 3: 計算 SHAP 值
                shap_pbar.set_description("⚡ 計算 SHAP 值")
                shap_values = self.shap_explainer.shap_values(X_sample)
                
                # 計算全域特徵重要性 (平均絕對 SHAP 值)
                mean_abs_shap = np.abs(shap_values).mean(0)
                feature_importance = list(zip(X.columns, mean_abs_shap))
                feature_importance.sort(key=lambda x: x[1], reverse=True)
                
                self.global_shap_values = feature_importance
                shap_pbar.update(1)
                
                shap_pbar.set_description("✅ SHAP 計算完成")
                shap_pbar.close()
                logger.info("SHAP 值計算完成")
            else:
                shap_pbar.close()
                logger.warning("沒有可用的 XGBoost 模型來計算 SHAP")
                
        except Exception as e:
            logger.warning(f"SHAP 值計算失敗: {str(e)}")
            self.global_shap_values = []
    
    def explain_prediction(self, X: pd.DataFrame) -> Tuple[np.ndarray, float]:
        """
        解釋單筆預測
        
        Args:
            X: 單筆特徵數據
            
        Returns:
            SHAP 值和基準值
        """
        if self.shap_explainer is None:
            raise ValueError("SHAP 解釋器未初始化")
        
        shap_values = self.shap_explainer.shap_values(X)
        base_value = self.shap_explainer.expected_value
        
        return shap_values[0], base_value
    
    def get_feature_importance(self) -> List[Tuple[str, float]]:
        """
        獲得特徵重要性 (基於 SHAP)
        
        Returns:
            特徵重要性列表
        """
        if self.global_shap_values is None:
            return []
        return self.global_shap_values
    
    def save_model(self, filepath: str):
        """
        保存模型
        
        Args:
            filepath: 保存路徑
        """
        model_data = {
            'base_models': self.base_models,
            'meta_model': self.meta_model,
            'cv_folds': self.cv_folds,
            'random_state': self.random_state,
            'lgb_params': self.lgb_params,
            'xgb_params': self.xgb_params,
            'is_fitted': self.is_fitted,
            'cv_scores': self.cv_scores,
            'global_shap_values': self.global_shap_values
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"模型已保存至: {filepath}")
    
    @classmethod
    def load_model(cls, filepath: str) -> 'StackingModel':
        """
        載入模型
        
        Args:
            filepath: 模型路徑
            
        Returns:
            載入的模型
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        # 創建新實例
        model = cls(
            cv_folds=model_data['cv_folds'],
            random_state=model_data['random_state']
        )
        
        # 恢復模型狀態
        model.base_models = model_data['base_models']
        model.meta_model = model_data['meta_model']
        model.lgb_params = model_data['lgb_params']
        model.xgb_params = model_data['xgb_params']
        model.is_fitted = model_data['is_fitted']
        model.cv_scores = model_data.get('cv_scores', {})
        model.global_shap_values = model_data.get('global_shap_values', [])
        
        # 重新初始化 SHAP 解釋器
        if model.base_models['xgb']:
            try:
                model.shap_explainer = shap.TreeExplainer(model.base_models['xgb'][0])
            except:
                logger.warning("無法重新初始化 SHAP 解釋器")
        
        logger.info(f"模型已從 {filepath} 載入")
        return model
    
    def get_cv_scores(self) -> Dict[str, float]:
        """
        獲取交叉驗證分數
        
        Returns:
            交叉驗證分數字典
        """
        if not self.is_fitted:
            logger.warning("模型尚未訓練，無法獲取 CV 分數")
            return {}
        
        return self.cv_scores
