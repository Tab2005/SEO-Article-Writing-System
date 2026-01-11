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

---

## [2026-01-11] 關鍵字研究（Research）Job 化：SERP → 抓全文 → 抽取 → 分析 → 落庫 → 後續產文可重用

### 目標
目前 Research 流程主要用 Google Custom Search 取得 SERP，並在同步分析時只把「標題/heading/字數」回傳前端；
本次調整要做到：

1. **抓到競品文章內容（正文純文字）**：Google CSE 只能拿到 title/snippet/link，正文必須另外對每個 link 進行爬取與抽取。
2. **每次搜尋打包成一個可追蹤的任務（Job）並持久化**：後續「產文/改寫/SEO 檢查」可直接指定 job_id 重用資料，不必重抓。
3. **可觀測性與可重跑**：任務狀態、進度、錯誤原因、結果快照可查詢。

### 範圍
**後端**
- 新增 Research Job 資料模型（DB）與 API
- Celery background 任務：SERP → crawl 多篇 → 產出 AnalysisReport + artifacts
- Crawler 抽取正文文字並落庫（API 回傳預設不帶全文，避免 payload 過大）

**前端**
- Research 頁改成：建立 job → 輪詢 job status/progress → 取 report 顯示

### 關鍵限制與策略
- Google Custom Search API **不提供全文**：只能拿到 SERP 資料；全文必須用 http client 抓網頁 HTML，再用抽取器/規則提取正文。
- 網站可能有：封鎖、地理限制、登入牆、JS 渲染。
  - MVP：先用 `httpx + BeautifulSoup` 抽純文字。
  - 進階（可選）：對「抓不到正文」的站再加 headless（Playwright）補強。
- Windows 本機跑 Celery：建議 `--pool=solo` 避免 prefork 問題。

### 資料模型（DB）
1. `research_jobs`
   - `id` (UUID)
   - `user_id` (UUID, nullable)
   - `keyword`, `market`, `depth`
   - `status`：pending / running / completed / failed / partial
   - `progress` (0-100), `message`
   - `settings_snapshot` (JSON)（這次跑用到的 Google/AI 設定快照，便於重現）
   - `created_at`, `started_at`, `completed_at`, `error`

2. `research_competitors`
   - `id` (UUID)
   - `job_id` (UUID)
   - SERP 欄位：`rank`, `url`, `serp_title`, `snippet`, `serp_fetched_at`
   - 爬取欄位：`fetch_status`（success/failed/skipped）、`http_status`, `error`
   - 抽取欄位：`page_title`, `meta_description`, `meta_keywords`, `headings`(JSON), `word_count`, `content_text`, `content_hash`, `scraped_at`

3. `research_artifacts`
   - `id` (UUID)
   - `job_id` (UUID)
   - `type`：analysis_report / topic_themes / custom
   - `payload` (JSON)
   - `created_at`, `version`

### API 設計（v1）
新增以 job 為核心的端點（保留既有同步 `/research/analyze` 作為 fallback）：

- `POST /api/v1/research/jobs`
  - 建立 job + 送入 Celery queue
  - 回傳 `job_id`、status、created_at

- `GET /api/v1/research/jobs/{job_id}`
  - 查詢狀態與進度（running/completed/failed）

- `GET /api/v1/research/jobs/{job_id}/report`
  - 回傳儲存的 `AnalysisReport`（完成後可取）

- `GET /api/v1/research/jobs/{job_id}/competitors`
  - 回傳競品清單（不含全文）

- `GET /api/v1/research/jobs/{job_id}/competitors/{rank}/content`
  - 回傳單篇正文（需要時才拉）

### 背景任務（Celery）
主任務：`run_research_job(job_id)`

1. 更新 job：running / progress 10
2. Google CSE 取 SERP（depth 筆）→ 寫入 `research_competitors`（SERP 欄位）→ progress 30
3. 逐篇 crawl + 抽取正文（並保存 headings/meta/word_count/content_text/hash）→ progress 30-90（依完成比例）
4. 用爬回的內容/結構生成 `AnalysisReport`（TF‑IDF 改用正文與結構）→ 寫入 `research_artifacts(type=analysis_report)` → progress 100
5. 更新 job：completed（或 partial/failed）

### 前端流程
- Research 頁送出：呼叫 `POST /research/jobs`
- 顯示進度條：每 2 秒輪詢 `GET /research/jobs/{job_id}`
- 完成後：呼叫 `GET /research/jobs/{job_id}/report` 顯示統計、TF‑IDF、H2/H3、競品列表

### 執行方式（本機）
1. 啟動 Redis（或用現有 redis_url）
2. 啟動後端 API
3. 啟動 Celery worker（Windows 建議 solo pool）

```bash
# backend API
cd backend
uvicorn app.main:app --reload --port 8000

# celery worker（Windows）
celery -A app.core.celery_app.celery_app worker -l info -Q research --pool=solo
```

### 驗收標準
- 建立 job 後能看到進度更新（running → completed）
- `report` 內容可重複取得（不依賴即時分析）
- 競品資料中含正文（單篇 content endpoint 可取），TF‑IDF/共現分析品質明顯提升


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
