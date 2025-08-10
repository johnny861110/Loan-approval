# 使用 Python 3.11 官方映像作為基礎（穩定且支援 NumPy 2.x）
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴和工具
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 安裝 uv 套件管理器
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# 設定環境變數
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=development
ENV MPLCONFIGDIR=/tmp/matplotlib

# 複製 uv 配置文件
COPY pyproject.toml uv.lock ./

# 安裝 Python 依賴（使用 uv 進行更快的安裝）
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# 複製應用程式代碼
COPY app/ app/

# 複製配置檔案
COPY config/ config/

# 創建必要目錄
RUN mkdir -p app/models logs outputs data/temp

# 創建非 root 用戶（安全性）
RUN groupadd -r appuser && useradd -r -g appuser appuser -m
RUN chown -R appuser:appuser /app && \
    mkdir -p /home/appuser/.cache && \
    chown -R appuser:appuser /home/appuser && \
    chmod -R 755 /home/appuser
USER appuser

# 設定 uv 快取目錄環境變數
# 設定 uv 環境變數
ENV UV_CACHE_DIR=/tmp/uv-cache
ENV UV_NO_CACHE=1

# 暴露端口
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 啟動命令（使用 uv 運行）
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
