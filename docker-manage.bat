@echo off
REM Docker 管理腳本 - 貸款審批系統

echo ================================
echo 貸款審批系統 - Docker 管理
echo ================================

if "%1"=="" goto help

if "%1"=="build" goto build
if "%1"=="up" goto up
if "%1"=="down" goto down
if "%1"=="logs" goto logs
if "%1"=="status" goto status
if "%1"=="clean" goto clean
if "%1"=="dev" goto dev
if "%1"=="prod" goto prod
if "%1"=="test" goto test
goto help

:build
echo [信息] 構建 Docker 映像...
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo [錯誤] 映像構建失敗
    exit /b 1
)
echo [完成] 映像構建成功
goto end

:up
echo [信息] 啟動服務...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [錯誤] 服務啟動失敗
    exit /b 1
)
echo [完成] 服務已啟動
docker-compose ps
goto show_urls

:down
echo [信息] 停止服務...
docker-compose down
echo [完成] 服務已停止
goto end

:logs
if "%2"=="" (
    echo [信息] 顯示所有服務日誌...
    docker-compose logs -f --tail=100
) else (
    echo [信息] 顯示 %2 服務日誌...
    docker-compose logs -f --tail=100 %2
)
goto end

:status
echo [信息] 服務狀態：
docker-compose ps
echo.
echo [信息] 資源使用情況：
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
goto end

:clean
echo [信息] 清理 Docker 資源...
docker-compose down -v
docker system prune -f
docker volume prune -f
echo [完成] 清理完成
goto end

:dev
echo [信息] 啟動開發環境...
docker-compose -f docker-compose.dev.yml up -d
if %errorlevel% neq 0 (
    echo [錯誤] 開發環境啟動失敗
    exit /b 1
)
echo [完成] 開發環境已啟動
docker-compose -f docker-compose.dev.yml ps
goto show_dev_urls

:prod
echo [信息] 啟動生產環境...
docker-compose -f docker-compose.prod.yml up -d
if %errorlevel% neq 0 (
    echo [錯誤] 生產環境啟動失敗
    exit /b 1
)
echo [完成] 生產環境已啟動
docker-compose -f docker-compose.prod.yml ps
goto show_prod_urls

:test
echo [信息] 運行測試...
docker-compose run --rm api python -m pytest tests/ -v
goto end

:show_urls
echo.
echo ================================
echo 可用服務：
echo ================================
echo - API 文檔: http://localhost:8000/docs
echo - API 重定向 UI: http://localhost:8000/redoc
echo - 健康檢查: http://localhost:8000/health
echo - Redis: localhost:6379
echo.
goto end

:show_dev_urls
echo.
echo ================================
echo 開發環境服務：
echo ================================
echo - API 文檔: http://localhost:8000/docs
echo - API 重定向 UI: http://localhost:8000/redoc
echo - 健康檢查: http://localhost:8000/health
echo - Flower 監控: http://localhost:5555 (需要啟用)
echo - Redis: localhost:6379
echo.
goto end

:show_prod_urls
echo.
echo ================================
echo 生產環境服務：
echo ================================
echo - 應用程式: http://localhost
echo - API 文檔: http://localhost/docs
echo - 健康檢查: http://localhost/health
echo - Flower 監控: http://localhost:5555 (如已啟用)
echo - Grafana: http://localhost:3000 (如已啟用)
echo.
goto end

:help
echo.
echo 用法: docker-manage.bat [命令]
echo.
echo 可用命令：
echo   build     - 構建 Docker 映像
echo   up        - 啟動服務 (使用 docker-compose.yml)
echo   down      - 停止服務
echo   logs      - 查看日誌 [可指定服務名稱]
echo   status    - 查看服務狀態和資源使用
echo   clean     - 清理所有 Docker 資源
echo   dev       - 啟動開發環境
echo   prod      - 啟動生產環境
echo   test      - 運行測試
echo.
echo 範例：
echo   docker-manage.bat build
echo   docker-manage.bat up
echo   docker-manage.bat logs api
echo   docker-manage.bat dev
echo.

:end
