"""
共用工具函數
"""

import os
import pickle
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 模型存儲目錄
MODELS_DIR = "app/models"

def ensure_models_directory():
    """確保模型目錄存在"""
    Path(MODELS_DIR).mkdir(parents=True, exist_ok=True)

def generate_model_id() -> str:
    """
    生成唯一的模型 ID
    
    Returns:
        模型 ID
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"model_{timestamp}_{unique_id}"

def get_model_path(model_id: str) -> str:
    """
    獲取模型檔案路徑
    
    Args:
        model_id: 模型 ID
        
    Returns:
        模型檔案路徑
    """
    ensure_models_directory()
    return os.path.join(MODELS_DIR, f"{model_id}.pkl")

def save_model(stacking_model, preprocessor, model_id: str) -> str:
    """
    保存完整的模型包（包含模型和預處理器）
    
    Args:
        stacking_model: Stacking 模型
        preprocessor: 數據預處理器
        model_id: 模型 ID
        
    Returns:
        保存的檔案路徑
    """
    ensure_models_directory()
    
    model_data = {
        'model': stacking_model,
        'preprocessor': preprocessor,
        'model_id': model_id,
        'created_at': datetime.now().isoformat(),
        'version': '1.0.0'
    }
    
    filepath = get_model_path(model_id)
    
    with open(filepath, 'wb') as f:
        pickle.dump(model_data, f)
    
    logger.info(f"模型已保存: {filepath}")
    return filepath

def load_model(model_id: str) -> Dict[str, Any]:
    """
    載入完整的模型包
    
    Args:
        model_id: 模型 ID
        
    Returns:
        包含模型和預處理器的字典
    """
    filepath = get_model_path(model_id)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"模型檔案不存在: {filepath}")
    
    with open(filepath, 'rb') as f:
        model_data = pickle.load(f)
    
    logger.info(f"模型已載入: {filepath}")
    return model_data

def list_available_models() -> list:
    """
    列出所有可用的模型
    
    Returns:
        模型列表
    """
    ensure_models_directory()
    
    models = []
    if os.path.exists(MODELS_DIR):
        for filename in os.listdir(MODELS_DIR):
            if filename.endswith('.pkl'):
                model_id = filename.replace('.pkl', '')
                filepath = os.path.join(MODELS_DIR, filename)
                
                try:
                    # 嘗試讀取模型元數據
                    with open(filepath, 'rb') as f:
                        model_data = pickle.load(f)
                    
                    models.append({
                        'model_id': model_id,
                        'created_at': model_data.get('created_at', 'Unknown'),
                        'version': model_data.get('version', 'Unknown'),
                        'file_size': os.path.getsize(filepath)
                    })
                except Exception as e:
                    logger.warning(f"無法讀取模型 {model_id}: {str(e)}")
    
    return models

def delete_model(model_id: str) -> bool:
    """
    刪除指定模型
    
    Args:
        model_id: 模型 ID
        
    Returns:
        是否成功刪除
    """
    filepath = get_model_path(model_id)
    
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            logger.info(f"模型已刪除: {filepath}")
            return True
        except Exception as e:
            logger.error(f"刪除模型失敗: {str(e)}")
            return False
    else:
        logger.warning(f"模型檔案不存在: {filepath}")
        return False

def save_json(data: Dict[str, Any], filepath: str):
    """
    保存 JSON 檔案
    
    Args:
        data: 要保存的數據
        filepath: 檔案路徑
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"JSON 檔案已保存: {filepath}")

def load_json(filepath: str) -> Dict[str, Any]:
    """
    載入 JSON 檔案
    
    Args:
        filepath: 檔案路徑
        
    Returns:
        載入的數據
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"JSON 檔案已載入: {filepath}")
    return data

def validate_csv_format(df, required_columns: list) -> tuple:
    """
    驗證 CSV 檔案格式
    
    Args:
        df: DataFrame
        required_columns: 必要欄位列表
        
    Returns:
        (is_valid, missing_columns, error_message)
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        error_msg = f"缺少必要欄位: {missing_columns}"
        return False, missing_columns, error_msg
    
    # 檢查數據類型
    numeric_columns = [
        'person_age', 'person_income', 'person_emp_length',
        'loan_amnt', 'loan_int_rate', 'loan_percent_income',
        'cb_person_cred_hist_length'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    error_msg = f"欄位 {col} 無法轉換為數值型"
                    return False, [], error_msg
    
    return True, [], ""

def get_model_performance_summary(model_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    獲取模型性能摘要
    
    Args:
        model_data: 模型數據
        
    Returns:
        性能摘要
    """
    stacking_model = model_data['model']
    
    summary = {
        'model_id': model_data.get('model_id', 'Unknown'),
        'created_at': model_data.get('created_at', 'Unknown'),
        'version': model_data.get('version', 'Unknown'),
        'cv_folds': getattr(stacking_model, 'cv_folds', 'Unknown'),
        'base_models': ['LightGBM', 'XGBoost'],
        'meta_model': 'Logistic Regression',
        'has_shap': hasattr(stacking_model, 'global_shap_values') and stacking_model.global_shap_values is not None
    }
    
    return summary

def format_shap_values(shap_values: list, feature_names: list, top_k: int = 10) -> list:
    """
    格式化 SHAP 值用於 API 回傳
    
    Args:
        shap_values: SHAP 值列表
        feature_names: 特徵名稱列表
        top_k: 返回前 k 個重要特徵
        
    Returns:
        格式化的特徵重要性列表
    """
    if len(shap_values) != len(feature_names):
        raise ValueError("SHAP 值和特徵名稱數量不匹配")
    
    # 組合並按絕對值排序
    feature_importance = list(zip(feature_names, shap_values))
    feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
    
    # 取前 k 個並格式化
    formatted_importance = []
    for feature, importance in feature_importance[:top_k]:
        formatted_importance.append([feature, float(importance)])
    
    return formatted_importance

def setup_logging(log_level: str = "INFO"):
    """
    設定日誌系統
    
    Args:
        log_level: 日誌級別
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log', encoding='utf-8')
        ]
    )

def calculate_prediction_confidence(probability: float) -> float:
    """
    計算預測信心度
    
    Args:
        probability: 預測機率
        
    Returns:
        信心度 (0-1)
    """
    return max(probability, 1 - probability)

def get_prediction_label(probability: float, threshold: float = 0.5) -> int:
    """
    根據機率和閾值獲取預測標籤
    
    Args:
        probability: 預測機率
        threshold: 分類閾值
        
    Returns:
        預測標籤 (0 或 1)
    """
    return int(probability >= threshold)

# 導入 pandas 用於數據驗證
try:
    import pandas as pd
except ImportError:
    pd = None
    logger.warning("pandas 未安裝，部分功能可能無法使用")

def health_check() -> Dict[str, Any]:
    """
    系統健康檢查
    
    Returns:
        健康狀態信息
    """
    status = {
        'timestamp': datetime.now().isoformat(),
        'models_directory': os.path.exists(MODELS_DIR),
        'available_models': len(list_available_models()),
        'disk_space': 'OK',  # 簡化版本
        'memory_usage': 'OK'  # 簡化版本
    }
    
    return status

def clean_old_models(max_models: int = 10):
    """
    清理舊模型（保留最新的 max_models 個）
    
    Args:
        max_models: 最大保留模型數量
    """
    models = list_available_models()
    
    if len(models) <= max_models:
        return
    
    # 按創建時間排序
    models.sort(key=lambda x: x['created_at'], reverse=True)
    
    # 刪除多餘的模型
    for model in models[max_models:]:
        delete_model(model['model_id'])
        logger.info(f"已刪除舊模型: {model['model_id']}")

def export_model_metadata(model_id: str) -> Dict[str, Any]:
    """
    導出模型元數據
    
    Args:
        model_id: 模型 ID
        
    Returns:
        模型元數據
    """
    try:
        model_data = load_model(model_id)
        
        metadata = {
            'model_id': model_id,
            'created_at': model_data.get('created_at'),
            'version': model_data.get('version'),
            'model_type': 'Stacking (LightGBM + XGBoost)',
            'preprocessing': model_data['preprocessor'].get_feature_info(),
            'performance': get_model_performance_summary(model_data)
        }
        
        return metadata
        
    except Exception as e:
        logger.error(f"導出模型元數據失敗: {str(e)}")
        return {}
