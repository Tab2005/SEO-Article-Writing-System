# SEO Article Writing System - 快速啟動指南

## ✅ 目錄結構已重整完成

所有檔案已移至正確位置：
- ✅ AI 服務整合至 `backend/app/services/`
- ✅ API 端點統一在 `backend/app/api/v1/endpoints/`
- ✅ Docker 配置移至 `docs/docker/` (可選)

## 🚀 快速啟動（本地開發模式）

### 1️⃣ 後端服務 (FastAPI)

```bash
# 進入後端目錄
cd backend

# 啟動開發伺服器 (SQLite 模式，無需額外資料庫)
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**後端 API 文件**: http://localhost:8000/docs

### 2️⃣ 前端服務 (React + Vite)

```bash
# 開啟新終端機，進入前端目錄
cd frontend

# 安裝依賴（首次執行）
npm install

# 啟動開發伺服器
npm run dev
```

**前端網頁**: http://localhost:5173

---

## 📝 環境配置

### 後端環境變數 (`backend/.env`)

```env
# 資料庫 (預設使用 SQLite，無需安裝 PostgreSQL)
DATABASE_URL=sqlite+aiosqlite:///./seo_article.db

# Redis (選用，用於快取和 Celery)
REDIS_URL=redis://localhost:6379/0

# 安全金鑰
SECRET_KEY=dev-secret-key-change-in-production

# AI API Keys (選填)
GOOGLE_API_KEY=your-google-api-key
OPENAI_API_KEY=your-openai-api-key
ZEABUR_AI_HUB_API_KEY=your-zeabur-key
```

### 前端環境變數 (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-google-client-id
```

---

## 🔧 進階設置（可選）

### 使用 PostgreSQL (生產環境推薦)

1. 安裝 PostgreSQL
2. 修改 `backend/.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/seo_article_db
   ```

### 使用 Redis (啟用快取功能)

1. 安裝 Redis
2. 確保 `backend/.env` 中 REDIS_URL 正確

### 背景任務處理 (Celery)

```bash
# 需要先啟動 Redis
..\.venv\Scripts\python.exe -m celery -A app.core.celery_app worker -l info
```

---

## 🐳 Docker 部署（可選）

如果你想使用 Docker 容器化部署，請參考 `docs/docker/README.md`

---

## 📚 相關資源

- [後端 API 文件](http://localhost:8000/docs)
- [專案架構說明](SEO 文章撰寫系統.md)
- [開發日誌](DEVLOG.md)
- [Docker 部署指南](docs/docker/README.md)

---

## 🆘 常見問題

### Q: 啟動後端時出現資料庫錯誤？
A: 確認 `.env` 中的 `DATABASE_URL` 設定正確，或使用預設的 SQLite 模式。

### Q: 前端無法連接後端 API？
A: 檢查前端 `.env` 中的 `VITE_API_URL` 是否為 `http://localhost:8000`

### Q: AI 功能無法使用？
A: 需要在後端 `.env` 中設定相應的 API Key (GOOGLE_API_KEY 或 ZEABUR_AI_HUB_API_KEY)
