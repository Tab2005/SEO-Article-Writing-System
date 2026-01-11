# SEO Article Writing System — Code-based Architecture Map

> 本文件**只依程式碼**整理（不依 README/其他 md）。

## 1) 整體分層

- Backend：FastAPI（`backend/app`）
  - `app/main.py`：App factory、CORS、lifespan、`/health`
  - `app/api/v1/*`：REST API 端點（v1）
  - `app/services/*`：商業邏輯（SERP、爬蟲、分析、LLM、SEO、設定快取）
  - `app/models/*`：SQLAlchemy models（User/Project/Article/SearchCache）
  - `app/schemas/*`：Pydantic API contract
  - `app/core/*`：DB、JWT、安全、WebSocket、例外

- Frontend：React + Vite（`frontend/src`）
  - `App.tsx`：路由（protected routes）
  - `pages/*`：頁面（Research/Content/SEO/Settings/Login…）
  - `services/*`：API 呼叫封裝（axios instance + feature services）
  - `store/*`：zustand（auth、theme…）

## 2) 後端入口與全域設定

- 入口：`backend/app/main.py`
  - lifespan：啟動時 `init_db()`（`Base.metadata.create_all`），關閉時 `close_db()`
  - CORS：debug 模式允許 `localhost:5173/3000`
  - Router：`/api/v1` 掛載 v1 routes
  - `GET /health`：回傳狀態/時間/DB 類型（sqlite/postgresql）

- 設定：`backend/app/config.py`
  - `Settings` 由 `.env` 載入（預設 debug=True、SQLite）

## 3) v1 API 路由總覽

路由聚合：`backend/app/api/v1/__init__.py`

### Authentication（`/api/v1/auth`）
- `POST /register`：建立使用者
- `POST /login`：email/password 登入，回 access/refresh token
- `POST /google`：Google OAuth access_token 登入（後端驗證 userinfo）
- `POST /logout`：把 token 加入 blacklist
- `POST /refresh`：refresh token 換新 token pair
- `GET /me`：取得目前使用者

Auth dependency：`backend/app/api/dependencies.py`
- debug 模式支援 `dev-access-token` bypass

### Research（`/api/v1/research`）
- `GET /serp`：Google Custom Search SERP
- `GET /analyze`：SERP → 爬蟲 → 競品分析報告（同步）
- `POST /analyze-themes`：把競品 H2 丟給 LLM 做語意主題（on-demand）
- `POST /keyword`、`GET /{task_id}`：任務制骨架（目前未接 Celery/DB tracking）

### Content（`/api/v1/content`）
- `POST /outline`：LLM 產大綱（可選先做競品 H2 統計）
- `POST /generate`：大綱 + 全文生成（Markdown）
- `POST /optimize`：文章 SEO 優化（改寫內容）

### SEO（`/api/v1/seo`）
- `POST /analyze`：SEO 分數與建議（規則檢查）

### Settings（`/api/v1/settings`）
- `GET /`：讀取目前設定（key 會 mask）
- `PUT /`：更新設定（只更新非空欄位），主要儲存在 Redis cache（長效）
- `POST /test/google-search`：測試 Google Custom Search API
- `POST /test/ai`：AI 連線測試（前端 Settings 頁會打）

### AI Hub（`/api/v1/ai`）
- `GET /providers`：取得可用 provider
- `GET /models`：取得 provider 對應模型
- `GET/POST /settings`：AI Hub 設定（另存 `system:ai_settings`）
- `POST /test-connection`：AI 連線測試
- `POST /analyze`：SSE 串流輸出分析結果

### WebSocket
- `GET ws /api/v1/ws`：可訂閱 task_id 進度（目前偏框架）

## 4) 核心資料流（後端）

### Research analyze pipeline
1. `GET /api/v1/research/analyze`
2. Google SERP：`services/google_search.py`
3. 競品爬蟲：`services/crawler_service.py`（BeautifulSoup+lxml，抽 title/headings/meta/字數）
4. 報告生成：`services/analysis_service.py`
   - 字數統計、共通 H2/H3、keyword 出現頻率
   - TF-IDF/共現/N-gram/TextRank：`services/tfidf_service.py`

### Content generation pipeline
1. `POST /api/v1/content/outline`（可選先做 SERP + 競品 H2）
2. `services/llm_service.py` 透過 Zeabur/Gemini client 產 JSON 大綱
3. `POST /api/v1/content/generate` 產全文 Markdown

### Settings pipeline
- 前端 `Settings.tsx` → `PUT /api/v1/settings` 寫入 Redis cache
- 目前（在你要求前）Google/LLM 的核心服務仍多從 `.env` 讀；下一步會把它們接到 Redis 設定（優先）

## 5) 資料模型（SQLAlchemy）

- `models/user.py`：使用者
- `models/project.py`：專案（擁有者/市場）
- `models/article.py`：文章（含 status/versioning、outline/secondary_keywords JSONB）
- `models/search_cache.py`：SERP/競品/報告快取（目前主要是 model 定義，尚未看到完整寫入/讀取流程）

## 6) 前端頁面與 API 對應

- Login：`pages/Login.tsx` → `POST /auth/google`（或 dev login）
- Research：`pages/Research.tsx` → `GET /research/analyze`、`POST /research/analyze-themes`
- ContentGeneration：`pages/ContentGeneration.tsx` → `POST /content/outline`、`POST /content/generate`、`POST /content/optimize`
- SEOChecker：`pages/SEOChecker.tsx` → `POST /seo/analyze`
- Settings：`pages/Settings.tsx` → `GET/PUT /settings`、`POST /settings/test/google-search`、`POST /settings/test/ai`、`GET /ai/providers`、`GET /ai/models`

- axios 與 token refresh：`services/api.ts`
- auth state：`store/authStore.ts`
