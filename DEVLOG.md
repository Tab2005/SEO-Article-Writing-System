# 開發紀錄 (Development Log)

## 專案資訊
- **專案名稱**: SEO 文章撰寫系統
- **開始日期**: 2026/01/07
- **技術棧**: FastAPI + React + TypeScript + PostgreSQL + Redis

---

## 2026/05/22 (今日)

### 🛠️ API 契約收斂與 Draft 持久化
- 修正了 `/health` 端點以包含 ISO-8601 `timestamp`，解決測試契約 drift。
- 在後端 SQLAlchemy `Article` 模型與 schemas 中新增 `brief_id`、`qa_status` 與 `qa_results` 等欄位，並套用 Alembic 遷移。
- 修改 `/content/draft` 路由強制實施 approved Brief 的約束。
- 前端寫作生成後，在背景自動關聯 approved Brief 保存為草稿 (Draft) 以作後續追溯。

### 📝 大綱編輯實質資料流串聯
- 前端將編輯後的大綱 (`editableSections`) 傳送回後端 `/generate` 端點。
- 後端接收到大綱後，跳過 AI 大綱生成，直接採用傳入的大綱進行文章段落撰寫。

### 🛡️ 實作 QA Gate V1 品質稽核
- 建立後端 `qa_service.py` 服務，對照網站定位與任務書，進行 Identity Fit、Restricted Angles、Info Gain 與 CTA Direction 四大指標的 LLM 評估。
- 新增 `POST /content/draft/{draft_id}/qa` 端點及對應的 `tests/test_qa.py` 單元測試。
- 前端新增了「AI 品質審查」UI 面板，展示稽核狀態、問題細項與優化建議，並支援重新審查。

### 📋 實作 Phase 5: Operational Layer (運作管理層)
- **內容佇列 (Content Queue)**：
  - 後端實作了 `GET /projects/{project_id}/content-queue` 端點，聚合關鍵字、任務書與草稿狀態。
  - 前端實作了 `ContentQueue.tsx`，支援高質感的 Kanban 與 Table 雙視圖切換及快速操作。
- **版本控制與變更軌跡 (Versioning & Rollback)**：
  - 後端實作了版本手動備份、列表查詢與一鍵還原 (Rollback) API，並在 `/generate` 文章寫作重新生成前自動執行舊草稿備份。
  - 前端於 ContentGeneration 頁面整合「版本歷史」側邊欄，支援一鍵回滾並與編輯器及字數即時同步。
- **預置示範數據 (Seed Demo Projects)**：
  - 後端編寫了 `seed_demo.py` 模擬數據，並在前端 Settings 頁面整合「一鍵預置」入口。

### 🧪 驗證與編譯
- 新增 `tests/test_versioning.py` 測試版本保存與還原。
- 修正 `tests/test_content_queue.py` 資料庫 schema 屬性不一致問題，以及 `test_list_draft_versions` 對回傳欄位的檢查斷言。
- 修正前端 `ContentQueue.tsx` 未使用的 React/ArrowRight 導入與錯誤的 LayoutKanban 圖標。
- 執行後端 pytest，全數 **27 Passed** 成功通過。
- 前端 `npm run build` 生產環境編譯成功，無任何 TypeScript 類型錯誤。

---

## 2026/01/09 (今日)

### 🎨 新增暗色模式切換
- 建立 `themeStore.ts` 主題狀態管理
- 建立 `ThemeToggle.tsx` 切換按鈕組件
- 更新 `tailwind.config.js` 啟用 class-based 暗色模式
- 更新 `index.css` 完整暗色模式樣式
- 側邊欄右上角新增月亮/太陽圖示切換

### ⚙️ 新增系統設定頁面
- 建立後端 `/api/v1/settings` API 端點
  - `GET /settings` - 取得設定（金鑰遮罩顯示）
  - `PUT /settings` - 更新設定
  - `POST /settings/test/google-search` - 測試 Google API
  - `POST /settings/test/openai` - 測試 OpenAI API
- 建立前端 `Settings.tsx` 設定頁面
  - Google Custom Search API 設定
  - OpenAI API 設定
  - Google OAuth 設定
  - 連線測試按鈕
  - 密碼顯示/隱藏功能

### 🔧 修正登入頁面
- 修正 Google OAuth 未設定時的錯誤
- 新增「開發者快速登入」按鈕（開發模式）
- 更新 `main.tsx` 條件式載入 GoogleOAuthProvider

### 📄 更新文件
- 更新 `SEO 文章撰寫系統.md` 反映所有已完成功能

---

## 2026/01/08

### Phase 5: 部署與優化 ✅
- **Docker 容器化**
  - 建立 `backend/Dockerfile`
  - 建立 `frontend/Dockerfile` (多階段建構)
  - 建立 `frontend/nginx.conf`
  - 建立 `docker-compose.yml` 完整編排
- **CI/CD 流程**
  - 建立 `.github/workflows/ci.yml` GitHub Actions
- **單元測試**
  - 建立 `tests/test_seo_checker.py`
  - 建立 `tests/test_api.py`
  - 建立 `pytest.ini` 配置

### Phase 4: 進階功能 ✅
- **WebSocket 即時推送**
  - 建立 `core/websocket.py` 連線管理器
  - 建立 `endpoints/websocket.py` WS 端點
- **SEO 分數檢查器**
  - 建立 `services/seo_checker.py` SEO 分析服務
  - 建立 `endpoints/seo.py` API 端點
  - 建立 `pages/SEOChecker.tsx` 前端頁面
- **資料匯出**
  - 建立 `utils/export.py` CSV/JSON 匯出

### Phase 3: 核心功能整合 ✅
- **Celery 背景任務**
  - 建立 `core/celery_app.py` Celery 配置
  - 建立 `tasks/research_tasks.py` 研究任務
  - 建立 `tasks/content_tasks.py` 內容生成任務
- **內容生成頁面**
  - 建立 `pages/ContentGeneration.tsx`
- **專案管理**
  - 建立 `pages/Projects.tsx`

### Phase 2: 前端基礎 ✅
- **React 專案初始化**
  - 使用 Vite + TypeScript
  - 設定 Tailwind CSS
  - 設定 React Router v6
- **Google OAuth 登入**
  - 建立 `pages/Login.tsx`
  - 整合 @react-oauth/google
- **狀態管理**
  - 建立 `store/authStore.ts` (Zustand)
  - 建立 `store/researchStore.ts`
- **API 服務層**
  - 建立 `services/api.ts` Axios 配置
  - 建立 `services/auth.service.ts`
  - 建立 `services/research.service.ts`
  - 建立 `services/content.service.ts`
- **React Query Hooks**
  - 建立 `hooks/useResearch.ts`
  - 建立 `hooks/useContent.ts`
- **頁面組件**
  - 建立 `pages/Dashboard.tsx`
  - 建立 `pages/Research.tsx`
  - 建立 `components/Layout.tsx`

---

## 2026/01/07

### Phase 1: 後端核心 ✅

#### Task 7: JWT 認證系統
- 建立 `core/security.py`
  - PasswordValidator: 密碼強度驗證
  - PasswordManager: bcrypt 加密
  - JWTManager: JWT 令牌管理
  - TokenBlacklist: 令牌黑名單
- 建立 `api/dependencies.py` 認證依賴
- 建立 `services/user_service.py` 用戶服務
- 建立 `endpoints/auth.py` 認證 API
- 新增 Google OAuth 支援 (`services/google_oauth.py`)

#### Task 6: Redis 快取 + OpenAI API
- 建立 `services/cache_manager.py` Redis 快取管理
- 建立 `services/llm_service.py` OpenAI API 整合
- 建立 `endpoints/content.py` 內容生成 API

#### Task 5: Google Search API + 爬蟲
- 建立 `services/google_search.py` 搜尋服務
- 建立 `services/crawler_service.py` 網頁爬蟲
- 建立 `services/analysis_service.py` 分析服務
- 建立 `endpoints/research.py` 研究 API

#### Task 3-4: 資料模型
- 建立 SQLAlchemy 模型
  - `models/user.py`
  - `models/project.py`
  - `models/article.py`
  - `models/search_cache.py`
- 建立 Pydantic Schemas
  - `schemas/user.py`
  - `schemas/project.py`
  - `schemas/article.py`
  - `schemas/research.py`
- 建立 Alembic 遷移配置

#### Task 1-2: 專案架構
- 建立 FastAPI 專案結構
- 建立 `config.py` 環境配置
- 建立 `core/database.py` 資料庫連線

---

## Git Commits 歷史

| Commit | 訊息 | 日期 |
|--------|------|------|
| `08eb66a` | Add dark mode toggle, fix login page, update documentation | 2026/01/09 |
| `e6f7df4` | Phase 5: Add Docker, CI/CD, and unit tests | 2026/01/08 |
| `3540986` | Phase 4: Add WebSocket, SEO checker, and export utilities | 2026/01/08 |
| `0168409` | Phase 3: Add Celery tasks, content generation, and project management | 2026/01/08 |
| `d91849d` | Task 9: Add research interface with API integration and state management | 2026/01/08 |
| `5850bf8` | Task 1-2: Establish FastAPI project architecture | 2026/01/07 |

---

## 待辦事項 (TODO)

### 高優先級
- [ ] 連接實際 PostgreSQL 資料庫
- [ ] 連接實際 Redis 服務
- [ ] 完善錯誤處理

### 中優先級
- [ ] 新增更多單元測試
- [ ] 實作密碼重設功能
- [ ] 批量內容生成

### 低優先級
- [ ] 多語言支援
- [ ] 資料分析儀表板
- [ ] 匯入/匯出專案

---

## 技術筆記

### 環境變數設定
```env
# Backend (.env)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/seo_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CX_ID=your-cx-id
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-secret
OPENAI_API_KEY=your-openai-key

# Frontend (.env.local)
VITE_GOOGLE_CLIENT_ID=your-oauth-client-id
```

### 本地開發指令
```bash
# 後端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev

# Docker
docker-compose up -d
```

---

**最後更新**: 2026/01/09 11:23
