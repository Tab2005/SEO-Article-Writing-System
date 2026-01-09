# SEO 文章撰寫系統 - 完整實作方案

## 專案概述

一個端到端的 SEO 內容生成平台，整合 Google Search API、OpenAI GPT 與競品分析功能。

**技術棧**: Python (FastAPI) + React (TypeScript) + PostgreSQL + Redis

**總開發時間**: 約 9-12 週

---

## Phase 1: 後端核心 (2-3 週)

### Task 1-2: FastAPI 專案架構

#### [NEW] `backend/` - 專案結構
```
backend/
├── app/
│   ├── main.py              # FastAPI 應用入口
│   ├── config.py            # 環境變數配置
│   ├── api/v1/              # API 路由層
│   ├── core/                # 核心邏輯層
│   ├── services/            # 業務邏輯層
│   ├── models/              # SQLAlchemy Models
│   ├── schemas/             # Pydantic Schemas
│   ├── tasks/               # Celery 背景任務
│   └── utils/               # 工具函數
├── tests/
├── alembic/
├── pyproject.toml
└── Dockerfile
```

#### 開發步驟
1. 使用 Poetry 初始化專案
2. 建立 FastAPI 應用入口與路由結構
3. 設定環境變數管理 (python-dotenv)

---

### Task 3-4: 資料庫與資料模型

#### [NEW] `backend/app/models/`
- `user.py` - 用戶模型 (密碼哈希、角色、統計)
- `project.py` - 專案模型 (用戶 → 專案 → 文章)
- `article.py` - 文章模型 (版本控制 + 元數據)
- `search_cache.py` - SERP 快取模型

#### 開發步驟
1. 設定 PostgreSQL 連線
2. 建立 SQLAlchemy Models
3. 設定 Alembic 資料庫遷移
4. 定義 Pydantic Schemas

---

### Task 5: Google Search API + 網頁爬蟲

#### [NEW] `backend/app/services/`
- `serp_service.py` - Google Custom Search API 封裝
- `crawler_service.py` - 網頁爬蟲邏輯 (httpx + BeautifulSoup)

#### 開發步驟
1. 整合 Google Custom Search API
2. 實現異步網頁爬蟲 (提取 H1-H3, meta 標籤)
3. 建立 Insight Aggregator (字數統計、標題頻率)

---

### Task 6: Redis 快取 + OpenAI 整合

#### [NEW] `backend/app/services/`
- `llm_service.py` - OpenAI API 封裝 (GPT-4o-mini)
- `cache_manager.py` - Redis 快取邏輯 (7天過期)

#### 開發步驟
1. 設定 Redis 連線
2. 實現搜尋結果快取策略
3. 整合 OpenAI GPT 生成大綱與內容

---

### Task 7: JWT 認證系統

#### [NEW] `backend/app/core/`
- `security.py` - 密碼加密 (bcrypt) + JWT 管理
- `dependencies.py` - 認證依賴注入

#### [NEW] `backend/app/api/v1/auth.py`
- `POST /auth/register` - 用戶註冊
- `POST /auth/login` - JWT 令牌生成
- `POST /auth/logout` - 令牌黑名單
- `POST /auth/refresh` - 令牌刷新
- `GET /auth/me` - 當前用戶資訊

---

## Phase 2: 前端基礎 (2 週)

### Task 8: 專案初始化與認證頁面

#### [NEW] `frontend/` - React 專案
```bash
npx -y create-vite@latest frontend -- --template react-ts
npm install tailwindcss zustand @tanstack/react-query axios react-router-dom
npm install react-hook-form zod lucide-react recharts
npx -y shadcn-ui@latest init
```

#### [NEW] 核心檔案
- `src/services/api.ts` - Axios 實例 + JWT Interceptor
- `src/services/auth.service.ts` - 認證 API 封裝
- `src/store/authStore.ts` - Zustand 認證狀態
- `src/pages/Login.tsx` - 登入頁面
- `src/pages/Register.tsx` - 註冊頁面

---

### Task 9: 關鍵字研究介面

#### [NEW] 核心組件
- `src/pages/Research.tsx` - 研究頁面
- `src/components/KeywordInput.tsx` - 關鍵字輸入
- `src/components/CompetitorCard.tsx` - 競品卡片
- `src/components/SEOMetrics.tsx` - 指標視覺化

---

## Phase 3: 核心功能整合 (2-3 週)

### Task 10: 背景任務系統
- Celery + Redis 佇列設定
- 批量爬蟲任務實現
- 前端輪詢/WebSocket 進度追蹤

### Task 11: 競品分析儀表板
- Recharts 圖表組件 (字數、關鍵字密度)
- 完整內容生成流程 UI

### Task 12: 編輯器與專案管理
- TipTap Markdown 編輯器
- 專案列表與詳情頁面
- 文章版本歷史

---

## Phase 4: 進階功能 (2 週)
- WebSocket 即時進度推送
- SEO 分數檢查器
- 批量內容生成
- 資料匯出 (CSV/JSON)

## Phase 5: 部署優化 (1-2 週)
- Docker Compose 容器化
- Nginx 反向代理 + SSL
- CI/CD Pipeline (GitHub Actions)
- 監控與日誌 (Sentry/ELK)

---

## 驗證計畫

### Phase 1 驗證
```bash
# 後端啟動測試
cd backend && poetry run uvicorn app.main:app --reload

# API 端點測試
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test@123456"}'
```

### Phase 2 驗證
```bash
cd frontend && npm run dev
# 瀏覽器開啟 http://localhost:5173 測試登入流程
```

---

## 時程摘要

| Phase | 預計時間 | 重點 |
|-------|----------|------|
| Phase 1 | 2-3 週 | 後端 API + 資料庫 + 認證 |
| Phase 2 | 2 週 | 前端基礎 + 認證頁面 |
| Phase 3 | 2-3 週 | 背景任務 + 儀表板 + 編輯器 |
| Phase 4 | 2 週 | 進階功能 |
| Phase 5 | 1-2 週 | 部署與優化 |

**總計**: 9-12 週
