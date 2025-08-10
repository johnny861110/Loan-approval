@echo off
REM 生產環境部署腳本 (Windows)

echo ================================
echo 貸款審批系統 - 生產環境部署
echo ================================

REM 檢查 Docker 是否運行
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] Docker 未運行或未安裝
    echo 請先安裝並啟動 Docker Desktop
    pause
    exit /b 1
)

REM 檢查環境變數檔案
if not exist .env.prod (
    echo [警告] 未找到 .env.prod 檔案
    echo 正在從範例檔案創建...
    copy .env.prod.example .env.prod
    echo [重要] 請編輯 .env.prod 檔案並填入正確的配置值
    pause
)

echo [信息] 正在構建生產環境映像...
docker-compose -f docker-compose.prod.yml --env-file .env.prod build

if %errorlevel% neq 0 (
    echo [錯誤] 映像構建失敗
    pause
    exit /b 1
)

echo [信息] 正在啟動生產環境服務...
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

if %errorlevel% neq 0 (
    echo [錯誤] 服務啟動失敗
    pause
    exit /b 1
)

echo.
echo ================================
echo 部署完成！
echo ================================
echo.
echo 服務狀態：
docker-compose -f docker-compose.prod.yml ps

echo.
echo 可用服務：
echo - API 文檔: http://localhost/docs
echo - 健康檢查: http://localhost/health
echo - Flower 監控: http://localhost:5555 (需要啟用監控)
echo - Grafana 儀表板: http://localhost:3000 (需要啟用監控)
echo.
echo 查看日誌：docker-compose -f docker-compose.prod.yml logs -f
echo 停止服務：docker-compose -f docker-compose.prod.yml down
echo.

pause
