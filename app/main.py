"""
FastAPI 主程式 - 提供模型訓練、預測和 SHAP 解釋 API
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd
import json
import uuid
import os
import io
from datetime import datetime
import pickle
import logging

from .model import StackingModel
from .preprocessing import DataPreprocessor, AdvancedDataPreprocessor
from .tasks import train_model_task
from .utils import save_model, load_model, get_model_path

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="Loan Approval Stacking API",
    description="基於 LightGBM + XGBoost Stacking 的貸款審批預測 API",
    version="1.0.0"
)

# 存儲訓練任務狀態
training_jobs = {}

# Pydantic 模型
class PredictionRequest(BaseModel):
    id: int
    person_age: float
    person_income: float
    person_emp_length: float
    loan_amnt: float
    loan_int_rate: float
    loan_percent_income: float
    cb_person_cred_hist_length: float
    person_home_ownership: str
    loan_intent: str
    loan_grade: str
    cb_person_default_on_file: str

class TrainingResponse(BaseModel):
    job_id: str
    status: str
    message: str

class PredictionResponse(BaseModel):
    id: int
    model_id: str
    probability: float
    label: int
    confidence: float

class SHAPGlobalResponse(BaseModel):
    model_id: str
    feature_importance: List[List[Any]]

class SHAPLocalResponse(BaseModel):
    id: int
    model_id: str
    features: List[str]
    shap_values: List[float]
    base_value: float

@app.get("/")
async def root():
    """API 根目錄"""
    return {
        "message": "Loan Approval Stacking API",
        "version": "1.0.0",
        "endpoints": {
            "train": "/v1/train/start",
            "status": "/v1/train/status/{job_id}",
            "predict": "/v1/predict?model_id=xxx",
            "predict_batch": "/v1/predict/batch",
            "shap_global": "/v1/shap/global?model_id=xxx",
            "shap_local": "/v1/shap/local?model_id=xxx",
            "shap_batch": "/v1/shap/batch",
            "list_models": "/v1/models",
            "docs": "/docs"
        },
        "data_requirements": {
            "upload_files": "必須包含 'id' 欄位，其他欄位用於特徵",
            "single_predict": "必須包含 'id' 欄位，以及所有特徵欄位",
            "batch_predict": "必須包含 'id' 欄位，其他欄位用於特徵",
            "output_mapping": "'id' 欄位會在所有預測和 SHAP 解釋的輸出中保留用於映射"
        }
    }

@app.post("/v1/train/start", response_model=TrainingResponse)
async def start_training(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_hyperopt: bool = False,
    cv_folds: int = 5
):
    """
    開始模型訓練任務
    
    Args:
        file: 訓練數據 CSV 檔案
        use_hyperopt: 是否使用 Hyperopt 優化超參數
        cv_folds: 交叉驗證折數
    """
    try:
        # 生成任務 ID
        job_id = str(uuid.uuid4())
        
        # 讀取上傳的 CSV 檔案
        content = await file.read()
        df = pd.read_csv(pd.io.common.StringIO(content.decode('utf-8')))
        
        # 驗證數據格式
        required_columns = [
            'person_age', 'person_income', 'person_emp_length',
            'loan_amnt', 'loan_int_rate', 'loan_percent_income',
            'cb_person_cred_hist_length', 'person_home_ownership',
            'loan_intent', 'loan_grade', 'cb_person_default_on_file',
            'loan_status'  # 目標變數
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"缺少必要欄位: {missing_columns}"
            )
        
        # 初始化任務狀態
        training_jobs[job_id] = {
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            "message": "任務已排入佇列"
        }
        
        # 啟動背景訓練任務
        background_tasks.add_task(
            train_model_task, 
            job_id, 
            df, 
            use_hyperopt, 
            cv_folds,
            training_jobs
        )
        
        logger.info(f"開始訓練任務: {job_id}")
        
        return TrainingResponse(
            job_id=job_id,
            status="STARTED",
            message="訓練任務已開始，請使用 job_id 查詢狀態"
        )
        
    except Exception as e:
        logger.error(f"訓練任務啟動失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/train/status/{job_id}")
async def get_training_status(job_id: str):
    """查詢訓練任務狀態"""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail="任務 ID 不存在")
    
    job_status = training_jobs[job_id]
    return {
        "job_id": job_id,
        **job_status
    }

@app.post("/v1/predict", response_model=PredictionResponse)
async def predict(
    data: PredictionRequest,
    model_id: str
):
    """
    單筆資料預測
    
    Args:
        data: 預測數據（包含 id 欄位）
        model_id: 模型 ID
    """
    try:
        # 載入模型
        model_path = get_model_path(model_id)
        if not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail="模型不存在")
        
        model_data = load_model(model_id)
        stacking_model = model_data['model']
        preprocessor = model_data['preprocessor']
        
        # 保存 id 用於回傳
        prediction_id = data.id
        
        # 準備數據
        input_df = pd.DataFrame([data.model_dump()])
        
        # 數據預處理
        X_processed = preprocessor.transform(input_df)
        
        # 預測
        probability = stacking_model.predict_proba(X_processed)[0]
        label = int(probability >= 0.5)
        confidence = max(probability, 1 - probability)
        
        return PredictionResponse(
            id=prediction_id,
            model_id=model_id,
            probability=float(probability),
            label=label,
            confidence=float(confidence)
        )
        
    except Exception as e:
        logger.error(f"預測失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/predict/batch")
async def predict_batch(
    file: UploadFile = File(...),
    model_id: str = Form(...)
):
    """
    批量預測端點
    
    Args:
        file: CSV 檔案包含 id 和特徵欄位
        model_id: 模型 ID
        
    Returns:
        CSV 檔案包含 id, prediction, probability
    """
    try:
        # 載入模型
        model_data = load_model(model_id)
        stacking_model = model_data['model']
        preprocessor = model_data['preprocessor']
        
        # 讀取檔案
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # 驗證必須有 id 欄位
        if 'id' not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="批量預測必須包含 'id' 欄位"
            )
        
        # 保存 id 用於映射
        ids = df['id'].copy()
        
        # 預處理數據 (不包含 id)
        X_processed = preprocessor.transform(df)
        
        # 進行預測
        predictions = stacking_model.predict(X_processed)
        probabilities = stacking_model.predict_proba(X_processed)
        
        # 處理概率值 - 如果是二元分類，取正類概率
        if probabilities.ndim == 2 and probabilities.shape[1] == 2:
            probabilities = probabilities[:, 1]
        elif probabilities.ndim == 1:
            # 如果是一維數組，直接使用
            probabilities = probabilities
        else:
            # 其他情況，使用第一列或整個數組
            probabilities = probabilities.ravel()
        
        # 創建結果 DataFrame，包含 id 映射
        result_df = pd.DataFrame({
            'id': ids,
            'prediction': predictions,
            'probability': probabilities
        })
        
        # 返回 CSV
        csv_buffer = io.StringIO()
        result_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=predictions.csv"}
        )
        
    except Exception as e:
        logger.error(f"批量預測失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/shap/global", response_model=SHAPGlobalResponse)
async def get_global_shap(model_id: str):
    """
    獲取全域 SHAP 特徵重要性
    
    Args:
        model_id: 模型 ID
    """
    try:
        # 載入模型
        model_data = load_model(model_id)
        stacking_model = model_data['model']
        
        if not hasattr(stacking_model, 'global_shap_values'):
            raise HTTPException(
                status_code=400, 
                detail="模型未計算 SHAP 值"
            )
        
        feature_importance = stacking_model.global_shap_values
        
        # 確保轉換為 Python 原生類型以避免序列化問題
        feature_importance_converted = []
        for item in feature_importance:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                feature_name = str(item[0])
                importance_value = float(item[1])
                feature_importance_converted.append([feature_name, importance_value])
            else:
                # 如果格式不符預期，直接轉換
                feature_importance_converted.append([str(item), 0.0])
        
        return SHAPGlobalResponse(
            model_id=model_id,
            feature_importance=feature_importance_converted
        )
        
    except Exception as e:
        logger.error(f"獲取全域 SHAP 失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/shap/local")
async def get_local_shap(
    data: PredictionRequest,
    model_id: str
):
    """
    獲取單筆預測的 SHAP 解釋
    
    Args:
        data: 預測數據（包含 id 欄位）
        model_id: 模型 ID
    """
    try:
        # 載入模型
        model_data = load_model(model_id)
        stacking_model = model_data['model']
        preprocessor = model_data['preprocessor']
        
        # 保存 id 用於回傳
        prediction_id = data.id
        
        # 準備數據
        input_df = pd.DataFrame([data.model_dump()])
        X_processed = preprocessor.transform(input_df)
        
        # 計算 SHAP 值
        shap_values, base_value = stacking_model.explain_prediction(X_processed)
        
        return SHAPLocalResponse(
            id=prediction_id,
            model_id=model_id,
            features=preprocessor.get_feature_names(),
            shap_values=shap_values.tolist(),
            base_value=float(base_value)
        )
        
    except Exception as e:
        logger.error(f"獲取 SHAP 解釋失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/shap/batch")
async def get_batch_shap(
    file: UploadFile = File(...),
    model_id: str = Form(...)
):
    """
    獲取批量 SHAP 解釋
    
    Args:
        file: CSV 檔案包含 id 和特徵欄位
        model_id: 模型 ID
        
    Returns:
        CSV 檔案包含 id 和 SHAP 值
    """
    try:
        # 載入模型
        model_data = load_model(model_id)
        stacking_model = model_data['model']
        preprocessor = model_data['preprocessor']
        
        # 讀取檔案
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # 驗證必須有 id 欄位
        if 'id' not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="批量 SHAP 解釋必須包含 'id' 欄位"
            )
        
        # 保存 id 用於映射
        ids = df['id'].copy()
        
        # 預處理數據 (不包含 id)
        X_processed = preprocessor.transform(df)
        
        # 計算 SHAP 值
        shap_explanations = []
        feature_names = preprocessor.get_feature_names()
        
        for i, row in enumerate(X_processed.values):
            row_reshaped = row.reshape(1, -1)
            shap_values, base_value = stacking_model.explain_prediction(row_reshaped)
            
            explanation = {
                'id': ids.iloc[i],
                'base_value': float(base_value)
            }
            
            # 添加每個特徵的 SHAP 值
            for j, feature_name in enumerate(feature_names):
                explanation[f'shap_{feature_name}'] = float(shap_values[j])
                
            shap_explanations.append(explanation)
        
        # 創建結果 DataFrame
        result_df = pd.DataFrame(shap_explanations)
        
        # 返回 CSV
        csv_buffer = io.StringIO()
        result_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=shap_explanations.csv"}
        )
        
    except Exception as e:
        logger.error(f"批量 SHAP 解釋失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """列出所有可用模型"""
    models_dir = "app/models"
    if not os.path.exists(models_dir):
        return {"models": []}
    
    models = []
    for filename in os.listdir(models_dir):
        if filename.endswith('.pkl'):
            model_id = filename.replace('.pkl', '')
            model_path = os.path.join(models_dir, filename)
            created_time = datetime.fromtimestamp(
                os.path.getctime(model_path)
            ).isoformat()
            
            models.append({
                "model_id": model_id,
                "created_at": created_time,
                "file_size": os.path.getsize(model_path)
            })
    
    return {"models": models}

@app.delete("/v1/models/{model_id}")
async def delete_model(model_id: str):
    """刪除指定模型"""
    model_path = get_model_path(model_id)
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="模型不存在")
    
    try:
        os.remove(model_path)
        return {"message": f"模型 {model_id} 已刪除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 健康檢查
@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "available_models": len(os.listdir("app/models")) if os.path.exists("app/models") else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
