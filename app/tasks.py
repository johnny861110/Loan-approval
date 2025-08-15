"""
優化後的非同步訓練任務
修正了超參數優化、pkg_resources 警告、多進程問題等
"""

import pandas as pd
import numpy as np
import os
import uuid
import pickle
import warnings
from datetime import datetime
import logging
from typing import Dict, Any
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import StackingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.metrics import roc_auc_score
from tqdm import tqdm
import sys
from celery import Celery

# 創建 Celery 應用程式實例
celery = Celery(
    'loan_approval_tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

# 解決 pkg_resources 警告
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pkg_resources")
warnings.filterwarnings("ignore", category=UserWarning, module="multiprocessing")

# HyperOpt 相關
try:
    from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
    HYPEROPT_AVAILABLE = True
except ImportError:
    HYPEROPT_AVAILABLE = False
    print("HyperOpt 未安裝，將跳過超參數優化")

# 模型相關
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("LightGBM 未安裝")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost 未安裝")

from .model import StackingModel
from .preprocessing import AdvancedDataPreprocessor
from .utils import save_model, generate_model_id

logger = logging.getLogger(__name__)

@celery.task
def optimize_hyperparameters_task(
    job_id: str,
    X: pd.DataFrame,
    y: pd.Series,
    n_trials: int = 50,
    training_jobs: Dict[str, Any] = None
):
    """
    優化後的超參數優化函數
    修正了搜索空間、目標函數和多進程問題
    
    Args:
        job_id: 任務 ID
        X: 特徵數據
        y: 目標變數
        n_trials: 優化試驗次數
        training_jobs: 任務狀態字典
    """
    try:
        if not HYPEROPT_AVAILABLE:
            logger.error("HyperOpt 未安裝，無法進行超參數優化")
            if training_jobs:
                training_jobs[job_id]["status"] = "FAILURE"
                training_jobs[job_id]["message"] = "HyperOpt 未安裝"
            return
        
        # 檢查模型可用性
        if not (LIGHTGBM_AVAILABLE and XGBOOST_AVAILABLE):
            logger.error("LightGBM 或 XGBoost 未安裝")
            if training_jobs:
                training_jobs[job_id]["status"] = "FAILURE"
                training_jobs[job_id]["message"] = "模型庫未安裝"
            return
        
        logger.info(f"開始使用 HyperOpt 進行超參數優化任務: {job_id}")
        
        if training_jobs:
            training_jobs[job_id]["status"] = "PROCESSING"
            training_jobs[job_id]["message"] = "正在使用 HyperOpt 優化超參數..."
        
        # 優化後的搜索空間 - 擴大參數範圍並增加多樣性
        space = {
            # LightGBM 超參數 - 使用離散選擇而非連續範圍
            'lgbm_n_estimators': hp.choice('lgbm_n_estimators', [100, 200, 300, 500, 800, 1000]),
            'lgbm_learning_rate': hp.loguniform('lgbm_learning_rate', np.log(0.01), np.log(0.3)),
            'lgbm_num_leaves': hp.choice('lgbm_num_leaves', [31, 63, 127, 255, 511]),
            'lgbm_max_depth': hp.choice('lgbm_max_depth', [-1, 3, 5, 7, 9, 12, 15]),
            'lgbm_min_child_samples': hp.choice('lgbm_min_child_samples', [10, 20, 50, 100]),
            'lgbm_subsample': hp.uniform('lgbm_subsample', 0.6, 1.0),
            'lgbm_colsample_bytree': hp.uniform('lgbm_colsample_bytree', 0.6, 1.0),
            'lgbm_reg_alpha': hp.loguniform('lgbm_reg_alpha', np.log(0.01), np.log(10)),
            'lgbm_reg_lambda': hp.loguniform('lgbm_reg_lambda', np.log(0.01), np.log(10)),
            
            # XGBoost 超參數 - 使用離散選擇
            'xgb_n_estimators': hp.choice('xgb_n_estimators', [100, 200, 300, 500, 800, 1000]),
            'xgb_learning_rate': hp.loguniform('xgb_learning_rate', np.log(0.01), np.log(0.3)),
            'xgb_max_depth': hp.choice('xgb_max_depth', [3, 4, 5, 6, 7, 8, 10]),
            'xgb_min_child_weight': hp.choice('xgb_min_child_weight', [1, 3, 5, 7]),
            'xgb_subsample': hp.uniform('xgb_subsample', 0.6, 1.0),
            'xgb_colsample_bytree': hp.uniform('xgb_colsample_bytree', 0.6, 1.0),
            'xgb_reg_alpha': hp.loguniform('xgb_reg_alpha', np.log(0.01), np.log(10)),
            'xgb_reg_lambda': hp.loguniform('xgb_reg_lambda', np.log(0.01), np.log(10)),
            'xgb_gamma': hp.loguniform('xgb_gamma', np.log(0.01), np.log(1)),
            
            # Meta Model 超參數
            'meta_C': hp.loguniform('meta_C', np.log(0.001), np.log(100)),
            'meta_solver': hp.choice('meta_solver', ['liblinear', 'lbfgs'])
        }
        
        # 數據預處理 - 減少 pickle 傳輸
        # 分層抽樣，確保類別平衡且減少數據量
        sample_size = min(3000, len(X))
        
        # 確保 train_size 不會是 1.0
        train_ratio = min(0.99, sample_size / len(X))
        
        if train_ratio < 1.0:
            X_sample, _, y_sample, _ = train_test_split(
                X, y, 
                train_size=train_ratio, 
                stratify=y, 
                random_state=42
            )
        else:
            # 如果樣本數量很小，直接使用全部數據
            X_sample, y_sample = X, y
        
        logger.info(f"使用 {len(X_sample)} 個樣本進行超參數優化（原始: {len(X)}）")
        
        # 優化的目標函數
        def objective(params):
            """優化後的 HyperOpt 目標函數"""
            try:
                # 設置隨機種子確保可重現性
                trial_seed = 42 + getattr(objective, 'trial_count', 0)
                np.random.seed(trial_seed)
                
                # 創建 LightGBM 模型
                lgbm_params = {
                    'n_estimators': params['lgbm_n_estimators'],
                    'learning_rate': params['lgbm_learning_rate'],
                    'num_leaves': params['lgbm_num_leaves'],
                    'max_depth': params['lgbm_max_depth'],
                    'min_child_samples': params['lgbm_min_child_samples'],
                    'subsample': params['lgbm_subsample'],
                    'colsample_bytree': params['lgbm_colsample_bytree'],
                    'reg_alpha': params['lgbm_reg_alpha'],
                    'reg_lambda': params['lgbm_reg_lambda'],
                    'random_state': trial_seed,
                    'verbosity': -1,
                    'class_weight': 'balanced',
                    'n_jobs': 1,  # 避免過度並行化
                    'device_type': 'cpu',  # 或 'gpu' 如果有 GPU
                    'force_row_wise': True  # 避免警告
                }
                
                lgbm = lgb.LGBMClassifier(**lgbm_params)
                
                # 創建 XGBoost 模型
                xgb_params = {
                    'n_estimators': params['xgb_n_estimators'],
                    'learning_rate': params['xgb_learning_rate'],
                    'max_depth': params['xgb_max_depth'],
                    'min_child_weight': params['xgb_min_child_weight'],
                    'subsample': params['xgb_subsample'],
                    'colsample_bytree': params['xgb_colsample_bytree'],
                    'reg_alpha': params['xgb_reg_alpha'],
                    'reg_lambda': params['xgb_reg_lambda'],
                    'gamma': params['xgb_gamma'],
                    'random_state': trial_seed,
                    'verbosity': 0,
                    'use_label_encoder': False,
                    'eval_metric': 'logloss',
                    'n_jobs': 1,  # 避免過度並行化
                    'tree_method': 'hist'  # 或 'gpu_hist' 如果有 GPU
                }
                
                xgb_model = xgb.XGBClassifier(**xgb_params)
                
                # Meta Model
                meta_params = {
                    'C': params['meta_C'],
                    'solver': params['meta_solver'],
                    'random_state': trial_seed,
                    'max_iter': 1000,
                    'n_jobs': 1
                }
                
                meta_model = LogisticRegression(**meta_params)
                
                # 創建 Stacking 分類器
                stack = StackingClassifier(
                    estimators=[('lgbm', lgbm), ('xgb', xgb_model)],
                    final_estimator=meta_model,
                    passthrough=False,
                    cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=trial_seed),
                    n_jobs=1,  # 避免過度並行化
                    verbose=0
                )
                
                # 交叉驗證評估
                cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=trial_seed)
                scores = cross_val_score(
                    stack, X_sample, y_sample, 
                    cv=cv, 
                    scoring='roc_auc',
                    n_jobs=1,  # 避免過度並行化
                    verbose=0
                )
                
                score = scores.mean()
                score_std = scores.std()
                
                # 更新進度
                current_trial = getattr(objective, 'trial_count', 0) + 1
                setattr(objective, 'trial_count', current_trial)
                
                if training_jobs:
                    progress = min(90, 30 + int(60 * current_trial / n_trials))
                    training_jobs[job_id]["progress"] = progress
                    training_jobs[job_id]["message"] = f"Trial {current_trial}/{n_trials} - AUC: {score:.4f}±{score_std:.4f}"
                
                # 記錄詳細信息
                logger.info(f"Trial {current_trial}: AUC = {score:.4f}±{score_std:.4f}")
                
                # 確保分數有意義的變化
                if score < 0.5:  # 如果分數太低，可能有問題
                    logger.warning(f"Trial {current_trial}: 異常低分數 {score:.4f}")
                
                return {
                    'loss': -score,  # 最小化負 AUC = 最大化 AUC
                    'status': STATUS_OK,
                    'eval_time': datetime.now(),
                    'score_std': score_std,
                    'params_hash': hash(str(sorted(params.items())))  # 參數唯一性檢查
                }
                
            except Exception as e:
                logger.error(f"Trial {getattr(objective, 'trial_count', 0) + 1} 執行錯誤: {str(e)}")
                return {'loss': 1.0, 'status': STATUS_OK}  # 對應 AUC = 0
        
        # 載入或創建 Trials 物件
        os.makedirs('models', exist_ok=True)
        trials_save_file = f'models/hyperopt_trials_{job_id}.pkl'
        
        if os.path.exists(trials_save_file):
            logger.info("載入現有的 trials 歷史...")
            try:
                with open(trials_save_file, 'rb') as f:
                    trials = pickle.load(f)
                logger.info(f"載入了 {len(trials.trials)} 個歷史試驗")
            except Exception as e:
                logger.warning(f"載入 trials 失敗: {e}，創建新的 trials")
                trials = Trials()
        else:
            trials = Trials()
        
        # 檢查歷史試驗的分數分布
        if trials.trials:
            trial_losses = [trial['result']['loss'] for trial in trials.trials if 'result' in trial]
            if trial_losses:
                logger.info(f"歷史試驗分數範圍: {min(trial_losses):.4f} 到 {max(trial_losses):.4f}")
                if len(set(trial_losses)) == 1:
                    logger.warning("所有歷史試驗分數相同，可能存在問題！")
        
        # 使用 TPE 進行超參數調整
        logger.info(f"開始 HyperOpt 優化，目標試驗次數: {n_trials}，當前已有: {len(trials.trials)}")
        
        remaining_trials = max(0, n_trials - len(trials.trials))
        
        if remaining_trials > 0:
            best = fmin(
                fn=objective,
                space=space,
                algo=tpe.suggest,
                max_evals=n_trials,
                trials=trials,
                verbose=True,
                rstate=np.random.default_rng(42),  # 使用新的隨機數生成器
                show_progressbar=False  # 避免與 tqdm 衝突
            )
            
            # 儲存 trials 歷史
            try:
                with open(trials_save_file, 'wb') as f:
                    pickle.dump(trials, f)
                logger.info(f"已儲存 trials 歷史到 {trials_save_file}")
            except Exception as e:
                logger.warning(f"儲存 trials 失敗: {e}")
        else:
            logger.info("已達到目標試驗次數，使用現有最佳結果")
            best = trials.argmin
        
        # 分析優化結果
        if trials.trials:
            trial_losses = [trial['result']['loss'] for trial in trials.trials if 'result' in trial]
            if trial_losses:
                best_score = -min(trial_losses)
                worst_score = -max(trial_losses)
                logger.info(f"優化結果統計:")
                logger.info(f"  最佳 AUC: {best_score:.4f}")
                logger.info(f"  最差 AUC: {worst_score:.4f}")
                logger.info(f"  改進幅度: {best_score - worst_score:.4f}")
                logger.info(f"  總試驗數: {len(trial_losses)}")
                logger.info(f"  不同分數數量: {len(set(trial_losses))}")
                
                # 檢查是否有有效的探索
                if len(set(trial_losses)) == 1:
                    logger.warning("⚠️  所有試驗分數相同，超參數優化可能沒有生效！")
                elif len(set(trial_losses)) < len(trial_losses) * 0.5:
                    logger.warning("⚠️  大部分試驗分數相同，搜索空間可能需要調整")
                else:
                    logger.info("✅  試驗分數有良好的多樣性，優化有效")
            
            best_trial = trials.best_trial
            best_score = -best_trial['result']['loss']
            
            # 處理最佳參數
            best_params = best_trial['misc']['vals']
            best_params_formatted = {}
            
            # 參數轉換映射
            choice_mappings = {
                'lgbm_n_estimators': [100, 200, 300, 500, 800, 1000],
                'lgbm_num_leaves': [31, 63, 127, 255, 511],
                'lgbm_max_depth': [-1, 3, 5, 7, 9, 12, 15],
                'lgbm_min_child_samples': [10, 20, 50, 100],
                'xgb_n_estimators': [100, 200, 300, 500, 800, 1000],
                'xgb_max_depth': [3, 4, 5, 6, 7, 8, 10],
                'xgb_min_child_weight': [1, 3, 5, 7],
                'meta_solver': ['liblinear', 'lbfgs']
            }
            
            for key, value in best_params.items():
                if isinstance(value, list) and len(value) > 0:
                    if key in choice_mappings:
                        choice_index = value[0]
                        best_params_formatted[key] = choice_mappings[key][choice_index]
                    else:
                        best_params_formatted[key] = value[0]
            
            # 添加模型類型
            best_params_formatted['model_type'] = 'stacking'
            
            # 創建結果字典
            result = {
                "best_params": best_params_formatted,
                "best_score": float(best_score),
                "n_trials": len(trials.trials),
                "optimization_method": "HyperOpt_TPE_Enhanced",
                "trials_file": trials_save_file,
                "completed_at": datetime.now().isoformat(),
                "score_variance": float(best_trial['result'].get('score_std', 0)),
                "exploration_diversity": len(set(trial_losses)) / len(trial_losses) if trial_losses else 0
            }
            
            if training_jobs:
                training_jobs[job_id]["status"] = "SUCCESS"
                training_jobs[job_id]["progress"] = 100
                training_jobs[job_id]["message"] = f"優化完成！最佳 AUC: {best_score:.4f} ({len(trials.trials)} trials)"
                training_jobs[job_id]["result"] = result
            
            logger.info(f"✅ HyperOpt 超參數優化任務 {job_id} 成功完成")
            logger.info(f"📊 最佳分數: {best_score:.4f}")
            logger.info(f"🔬 總試驗次數: {len(trials.trials)}")
            logger.info(f"🎯 最佳參數: {best_params_formatted}")
            
            # 返回優化結果
            return result
            
        else:
            raise Exception("沒有成功的試驗")
        
    except Exception as e:
        error_msg = f"HyperOpt 超參數優化失敗: {str(e)}"
        logger.error(f"❌ 任務 {job_id} - {error_msg}")
        
        if training_jobs:
            training_jobs[job_id]["status"] = "FAILURE"
            training_jobs[job_id]["message"] = error_msg
            training_jobs[job_id]["error"] = str(e)


@celery.task
def train_model_task(
    job_id: str, 
    df: pd.DataFrame, 
    use_hyperopt: bool = False,
    cv_folds: int = 5,
    training_jobs: Dict[str, Any] = None
):
    """
    優化後的模型訓練任務
    
    Args:
        job_id: 任務 ID
        df: 訓練數據
        use_hyperopt: 是否使用超參數優化
        cv_folds: 交叉驗證折數
        training_jobs: 任務狀態字典
    """
    try:
        logger.info(f"🚀 開始執行訓練任務: {job_id}")
        
        # 創建總體任務進度條
        task_pbar = tqdm(
            total=6,
            desc="🚀 模型訓練管線",
            unit="階段",
            ncols=100,
            file=sys.stdout
        )
        
        try:
            # 階段 1: 數據預處理
            task_pbar.set_description("🔧 數據預處理階段")
            if training_jobs:
                training_jobs[job_id]["status"] = "PROCESSING"
                training_jobs[job_id]["progress"] = 10
                training_jobs[job_id]["current_step"] = "Data Preprocessing"
                training_jobs[job_id]["message"] = "正在預處理數據..."
            
            # 數據預處理
            preprocessor = AdvancedDataPreprocessor(create_interactions=True)
            X, y = preprocessor.fit_transform_with_target(df)
            
            logger.info(f"✅ 數據預處理完成，特徵數量: {X.shape[1]}")
            task_pbar.update(1)
            
            # 階段 2: 超參數優化（如果啟用）
            optimized_params = None
            if use_hyperopt:
                task_pbar.set_description("⚙️ 超參數優化階段")
                if training_jobs:
                    training_jobs[job_id]["progress"] = 20
                    training_jobs[job_id]["current_step"] = "Hyperparameter Optimization"
                    training_jobs[job_id]["message"] = "正在進行超參數優化..."
                
                logger.info("🔬 使用 HyperOpt 優化超參數...")
                
                # 執行超參數優化並獲取結果
                hyperopt_job_id = f"{job_id}_hyperopt"
                
                # 初始化超參數優化任務狀態
                if training_jobs:
                    training_jobs[hyperopt_job_id] = {
                        "status": "PROCESSING",
                        "created_at": datetime.now().isoformat(),
                        "progress": 0,
                        "message": "開始超參數優化..."
                    }
                
                # 直接調用超參數優化函數並獲取結果
                optimize_result = optimize_hyperparameters_task(
                    hyperopt_job_id, X, y, n_trials=50, training_jobs=training_jobs
                )
                
                # 檢查優化結果
                if optimize_result and 'best_params' in optimize_result:
                    optimized_params = optimize_result['best_params']
                    logger.info(f"✅ 超參數優化完成: {optimized_params}")
                else:
                    logger.warning("⚠️ 超參數優化失敗，將使用預設參數")
                
                task_pbar.update(1)
            else:
                logger.info("⏭️  跳過超參數優化階段")
                task_pbar.update(1)  # 跳過超參數優化階段
            
            # 階段 3: 模型配置
            task_pbar.set_description("🔧 配置模型架構")
            if training_jobs:
                training_jobs[job_id]["progress"] = 40
                training_jobs[job_id]["current_step"] = "Model Configuration"
                training_jobs[job_id]["message"] = "正在配置模型架構..."
            
            # 創建和配置模型
            stacking_model = StackingModel(cv_folds=cv_folds)
            
            if optimized_params:
                logger.info(f"🎯 使用優化後的超參數: {optimized_params}")
                
                # 更新 LightGBM 參數
                lgb_updates = {}
                for key, value in optimized_params.items():
                    if key.startswith('lgbm_'):
                        param_name = key.replace('lgbm_', '')
                        if param_name in ['n_estimators', 'num_leaves', 'max_depth', 
                                         'min_child_samples']:
                            lgb_updates[param_name] = int(value)
                        else:
                            lgb_updates[param_name] = value
                
                if lgb_updates:
                    stacking_model.lgb_params.update(lgb_updates)
                    logger.info(f"📊 LightGBM 參數已更新: {lgb_updates}")
                
                # 更新 XGBoost 參數
                xgb_updates = {}
                for key, value in optimized_params.items():
                    if key.startswith('xgb_'):
                        param_name = key.replace('xgb_', '')
                        if param_name in ['n_estimators', 'max_depth', 'min_child_weight']:
                            xgb_updates[param_name] = int(value)
                        else:
                            xgb_updates[param_name] = value
                
                if xgb_updates:
                    stacking_model.xgb_params.update(xgb_updates)
                    logger.info(f"🚀 XGBoost 參數已更新: {xgb_updates}")
                
                # 更新 Meta Model
                if 'meta_C' in optimized_params:
                    stacking_model.meta_model = LogisticRegression(
                        C=optimized_params['meta_C'],
                        solver=optimized_params.get('meta_solver', 'lbfgs'),
                        random_state=42,
                        max_iter=1000
                    )
                    logger.info(f"🎯 Meta Model 參數已更新: C={optimized_params['meta_C']}")
            else:
                logger.info("ℹ️ 使用預設超參數")
            
            task_pbar.update(1)
            
            # 階段 4: 模型訓練
            task_pbar.set_description("🚀 模型訓練階段")
            if training_jobs:
                training_jobs[job_id]["progress"] = 60
                training_jobs[job_id]["current_step"] = "Model Training"
                training_jobs[job_id]["message"] = "正在訓練模型..."
            
            # 訓練模型
            stacking_model.fit(X, y)
            
            logger.info("✅ 模型訓練完成")
            task_pbar.update(1)
            
            # 階段 5: 保存模型
            task_pbar.set_description("💾 保存模型")
            if training_jobs:
                training_jobs[job_id]["progress"] = 80
                training_jobs[job_id]["current_step"] = "Model Saving"
                training_jobs[job_id]["message"] = "正在保存模型..."
            
            # 生成模型 ID 並保存
            model_id = generate_model_id()
            save_model(stacking_model, preprocessor, model_id)
            
            logger.info(f"✅ 模型已保存，模型 ID: {model_id}")
            task_pbar.update(1)
            
            # 階段 6: 性能評估
            task_pbar.set_description("📊 性能評估")
            if training_jobs:
                training_jobs[job_id]["progress"] = 90
                training_jobs[job_id]["current_step"] = "Performance Evaluation"
                training_jobs[job_id]["message"] = "正在評估模型性能..."
            
            # 計算交叉驗證分數
            cv_scores = stacking_model.get_cv_scores()
            
            # 更新任務完成狀態
            result = {
                "model_id": model_id,
                "cv_scores": cv_scores,
                "feature_count": X.shape[1],
                "training_samples": len(X),
                "hyperopt_used": use_hyperopt,
                "optimized_params": optimized_params,  # 添加優化參數
                "cv_folds": cv_folds,
                "completed_at": datetime.now().isoformat()
            }
            
            if training_jobs:
                training_jobs[job_id]["status"] = "SUCCESS"
                training_jobs[job_id]["progress"] = 100
                training_jobs[job_id]["current_step"] = "Completed"
                training_jobs[job_id]["message"] = f"✅ 訓練完成！模型 ID: {model_id}"
                training_jobs[job_id]["result"] = result
            
            task_pbar.update(1)
            logger.info(f"🎉 模型訓練任務 {job_id} 完成，模型 ID: {model_id}")
            
        finally:
            task_pbar.close()
            
    except Exception as e:
        error_msg = f"模型訓練失敗: {str(e)}"
        logger.error(f"❌ 任務 {job_id} - {error_msg}")
        
        if training_jobs:
            training_jobs[job_id]["status"] = "FAILURE"
            training_jobs[job_id]["message"] = error_msg
            training_jobs[job_id]["error"] = str(e)
        
        # 確保進度條關閉
        try:
            task_pbar.close()
        except:
            pass


@celery.task
def batch_prediction_task(
    job_id: str,
    model_id: str,
    input_file: str,
    output_file: str,
    training_jobs: Dict[str, Any] = None
):
    """
    批次預測任務
    
    Args:
        job_id: 任務 ID
        model_id: 模型 ID
        input_file: 輸入檔案路徑
        output_file: 輸出檔案路徑
        training_jobs: 任務狀態字典
    """
    try:
        from .utils import load_model
        
        logger.info(f"🔮 開始執行批次預測任務: {job_id}")
        
        if training_jobs:
            training_jobs[job_id]["status"] = "PROCESSING"
            training_jobs[job_id]["progress"] = 10
            training_jobs[job_id]["message"] = "正在載入模型..."
        
        # 載入模型
        model, preprocessor = load_model(model_id)
        
        if training_jobs:
            training_jobs[job_id]["progress"] = 30
            training_jobs[job_id]["message"] = "正在載入預測數據..."
        
        # 載入預測數據
        df = pd.read_csv(input_file)
        
        if training_jobs:
            training_jobs[job_id]["progress"] = 50
            training_jobs[job_id]["message"] = "正在進行數據預處理..."
        
        # 預處理數據
        X = preprocessor.transform(df)
        
        if training_jobs:
            training_jobs[job_id]["progress"] = 70
            training_jobs[job_id]["message"] = "正在進行預測..."
        
        # 進行預測
        predictions = model.predict_proba(X)[:, 1]
        
        if training_jobs:
            training_jobs[job_id]["progress"] = 90
            training_jobs[job_id]["message"] = "正在保存預測結果..."
        
        # 保存預測結果
        result_df = df.copy()
        result_df['prediction'] = predictions
        result_df.to_csv(output_file, index=False)
        
        # 更新任務狀態
        result = {
            "model_id": model_id,
            "input_file": input_file,
            "output_file": output_file,
            "prediction_count": len(predictions),
            "completed_at": datetime.now().isoformat()
        }
        
        if training_jobs:
            training_jobs[job_id]["status"] = "SUCCESS"
            training_jobs[job_id]["progress"] = 100
            training_jobs[job_id]["message"] = f"✅ 預測完成！處理了 {len(predictions)} 筆數據"
            training_jobs[job_id]["result"] = result
        
        logger.info(f"🎉 批次預測任務 {job_id} 完成")
        
    except Exception as e:
        error_msg = f"批次預測失敗: {str(e)}"
        logger.error(f"❌ 任務 {job_id} - {error_msg}")
        
        if training_jobs:
            training_jobs[job_id]["status"] = "FAILURE"
            training_jobs[job_id]["message"] = error_msg
            training_jobs[job_id]["error"] = str(e)
