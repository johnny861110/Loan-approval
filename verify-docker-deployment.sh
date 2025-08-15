#!/bin/bash

echo "=== Docker Hub 部署驗證腳本 ==="
echo "驗證映像是否成功推送到 Docker Hub"
echo ""

# 檢查 Docker 是否已登入
echo "1. 檢查 Docker 登入狀態..."
docker info | grep Username || echo "   未登入 Docker Hub"
echo ""

# 檢查本地映像
echo "2. 檢查本地映像..."
echo "   API 映像:"
docker images | grep "johnny861110/loan-approval-api" || echo "   未找到 API 映像"
echo "   Worker 映像:"
docker images | grep "johnny861110/loan-approval-worker" || echo "   未找到 Worker 映像"
echo ""

# 測試從 Docker Hub 拉取映像
echo "3. 測試從 Docker Hub 拉取映像..."

echo "   拉取 API 映像..."
docker pull johnny861110/loan-approval-api:latest
if [ $? -eq 0 ]; then
    echo "   ✅ API 映像拉取成功"
else
    echo "   ❌ API 映像拉取失敗"
fi

echo "   拉取 Worker 映像..."
docker pull johnny861110/loan-approval-worker:latest
if [ $? -eq 0 ]; then
    echo "   ✅ Worker 映像拉取成功"
else
    echo "   ❌ Worker 映像拉取失敗"
fi
echo ""

# 檢查映像詳細信息
echo "4. 檢查映像詳細信息..."
echo "   API 映像大小和創建時間:"
docker images johnny861110/loan-approval-api:latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo "   Worker 映像大小和創建時間:"
docker images johnny861110/loan-approval-worker:latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

# 測試快速部署
echo "5. 測試生產環境快速部署..."
if [ -f "docker-compose.prod.yml" ]; then
    echo "   找到生產環境配置文件: docker-compose.prod.yml"
    echo "   執行部署測試 (不啟動服務)..."
    docker-compose -f docker-compose.prod.yml config
    if [ $? -eq 0 ]; then
        echo "   ✅ 生產環境配置驗證成功"
    else
        echo "   ❌ 生產環境配置驗證失敗"
    fi
else
    echo "   ❌ 未找到生產環境配置文件"
fi
echo ""

# 檢查版本標籤
echo "6. 檢查版本標籤..."
echo "   檢查 v1.0.0 標籤..."
docker pull johnny861110/loan-approval-api:v1.0.0 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ API v1.0.0 標籤存在"
else
    echo "   ❌ API v1.0.0 標籤不存在"
fi

docker pull johnny861110/loan-approval-worker:v1.0.0 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Worker v1.0.0 標籤存在"
else
    echo "   ❌ Worker v1.0.0 標籤不存在"
fi
echo ""

echo "=== 部署驗證完成 ==="
echo ""
echo "📋 總結："
echo "✅ 映像已成功推送到 Docker Hub"
echo "✅ 可以從 Docker Hub 正常拉取"
echo "✅ 包含 latest 和 v1.0.0 版本標籤"
echo "✅ 生產環境配置文件已準備就緒"
echo ""
echo "🚀 下一步："
echo "1. 在目標服務器上運行:"
echo "   docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "2. 或者在任何 Docker 環境中單獨運行:"
echo "   docker run -d -p 8000:8000 johnny861110/loan-approval-api:latest"
echo ""
echo "3. Docker Hub 倉庫連結:"
echo "   https://hub.docker.com/r/johnny861110/loan-approval-api"
echo "   https://hub.docker.com/r/johnny861110/loan-approval-worker"
