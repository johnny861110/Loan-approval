@echo off
REM 生產環境管理腳本 (Windows)

if "%1"=="" goto help

if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="status" goto status
if "%1"=="logs" goto logs
if "%1"=="update" goto update
if "%1"=="backup" goto backup
if "%1"=="monitor" goto monitor
if "%1"=="health" goto health
goto help

:start
echo [信息] 啟動生產環境服務...
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
goto end

:stop
echo [信息] 停止生產環境服務...
docker-compose -f docker-compose.prod.yml --env-file .env.prod down
goto end

:restart
echo [信息] 重啟生產環境服務...
docker-compose -f docker-compose.prod.yml --env-file .env.prod restart
goto end

:status
echo [信息] 服務狀態：
docker-compose -f docker-compose.prod.yml ps
echo.
echo [信息] 資源使用情況：
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
goto end

:logs
if "%2"=="" (
    docker-compose -f docker-compose.prod.yml logs -f --tail=100
) else (
    docker-compose -f docker-compose.prod.yml logs -f --tail=100 %2
)
goto end

:update
echo [信息] 更新生產環境...
echo [1/4] 拉取最新代碼...
git pull
echo [2/4] 重新構建映像...
docker-compose -f docker-compose.prod.yml --env-file .env.prod build
echo [3/4] 重啟服務...
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
echo [4/4] 清理舊映像...
docker image prune -f
echo [完成] 更新完成！
goto end

:backup
echo [信息] 備份數據...
set backup_dir=backups\%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%
mkdir %backup_dir% 2>nul
docker-compose -f docker-compose.prod.yml exec -T api python -c "import shutil; shutil.make_archive('backup', 'zip', '/app/app/models')" 
echo [完成] 備份已保存到 %backup_dir%
goto end

:monitor
echo [信息] 啟動監控服務...
docker-compose -f docker-compose.prod.yml --env-file .env.prod --profile monitoring up -d
echo [完成] 監控服務已啟動
echo - Flower: http://localhost:5555
echo - Prometheus: http://localhost:9090
echo - Grafana: http://localhost:3000
goto end

:health
echo [信息] 健康檢查...
echo.
echo API 健康狀態：
curl -s http://localhost/health | python -m json.tool 2>nul || echo "API 無回應"
echo.
echo Redis 狀態：
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping 2>nul || echo "Redis 無回應"
echo.
echo 服務狀態：
docker-compose -f docker-compose.prod.yml ps
goto end

:help
echo.
echo 生產環境管理腳本
echo.
echo 用法: prod-manage.bat [命令]
echo.
echo 可用命令：
echo   start     - 啟動所有服務
echo   stop      - 停止所有服務
echo   restart   - 重啟所有服務
echo   status    - 查看服務狀態和資源使用
echo   logs      - 查看服務日誌 (可指定服務名稱)
echo   update    - 更新並重新部署
echo   backup    - 備份重要數據
echo   monitor   - 啟動監控服務
echo   health    - 健康檢查
echo.
echo 範例：
echo   prod-manage.bat start
echo   prod-manage.bat logs api
echo   prod-manage.bat status
echo.

:end
