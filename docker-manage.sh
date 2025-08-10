#!/bin/bash

# Docker 容器管理腳本

case "$1" in
    "start")
        echo "🚀 啟動貸款審批系統..."
        docker-compose up -d
        echo "✅ 系統啟動完成"
        ;;
    "stop")
        echo "🛑 停止貸款審批系統..."
        docker-compose down
        echo "✅ 系統已停止"
        ;;
    "status")
        echo "📊 系統狀態："
        docker-compose ps
        ;;
    "logs")
        echo "📜 查看系統日誌："
        docker-compose logs -f --tail=50
        ;;
    "health")
        echo "🔍 健康檢查："
        echo "API: $(curl -s http://localhost:8000/health | grep -o '"status":"[^"]*"')"
        echo "Worker ping:"
        docker exec loan-approval-worker-1 celery -A app.tasks inspect ping 2>/dev/null | grep -A1 "OK"
        ;;
    "rebuild")
        echo "🔨 重建系統..."
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        echo "✅ 重建完成"
        ;;
    *)
        echo "用法: $0 {start|stop|status|logs|health|rebuild}"
        echo "  start   - 啟動系統"
        echo "  stop    - 停止系統"
        echo "  status  - 查看容器狀態"
        echo "  logs    - 查看系統日誌"
        echo "  health  - 執行健康檢查"
        echo "  rebuild - 重建並重新啟動系統"
        exit 1
        ;;
esac
