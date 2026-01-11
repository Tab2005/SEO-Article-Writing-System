# Docker 部署選項（可選）

本專案已優化為本地開發模式，Docker 配置已移至此處作為可選的部署參考。

## 使用 Docker 部署（可選）

如果你想使用 Docker 容器化部署，可以參考以下檔案：

- `docker-compose.yml.example` - Docker Compose 配置範例
- `backend.Dockerfile.example` - 後端 Dockerfile 範例
- `frontend.Dockerfile.example` - 前端 Dockerfile 範例

## 啟動 Docker 服務

```bash
# 1. 複製配置檔案
cp docker-compose.yml.example ../docker-compose.yml
cp backend.Dockerfile.example ../backend/Dockerfile
cp frontend.Dockerfile.example ../frontend/Dockerfile

# 2. 回到專案根目錄
cd ../..

# 3. 啟動所有服務
docker compose up --build
```

## 服務端口

- Frontend: http://localhost (port 80)
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## 注意事項

Docker 模式適合：
- 生產環境部署
- 快速演示
- 團隊統一環境

本地開發模式更適合：
- 日常開發（啟動更快）
- 除錯和測試
- 靈活的依賴管理
