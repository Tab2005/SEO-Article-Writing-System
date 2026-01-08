# **SEO 文章撰寫系統：系統結構設計文件 (SSD)**

## **1\. 系統架構概覽 (Architecture Overview)**

本系統採用 **模組化架構**，確保研究、分析、撰寫與儲存四個核心功能解耦。

### **核心模組圖解**

1. **用戶介面 (UI Layer)**: 接收關鍵字輸入，顯示研究報告與生成文章。  
2. **研究模組 (Research Engine)**: 負責搜尋結果抓取與網頁內容爬取。  
3. **分析模組 (Analysis Engine)**: 提取關鍵字、標題結構、字數統計。  
4. **內容生成模組 (Content Generator)**: 串接 LLM (GPT-4o/Gemini) 生成大綱與內文。  
5. **儲存與快取層 (Data & Cache)**: 儲存搜尋結果以節省 API 費用。

## **2\. 階段 1：研究與競品分析流程 (Detailed Data Flow)**

這是目前開發的重點區塊，資料流向如下：

1. **Keyword Input**: 用戶輸入目標關鍵字。  
2. **SERP Fetcher**: 呼叫 Google Custom Search API。  
   * *Input*: Keyword, API Key, CX ID.  
   * *Output*: List of Objects (Title, Link, Snippet).  
3. **Content Crawler**: 對前 10 名網址進行異步爬取。  
   * *Logic*: 提取 \<h1\> 到 \<h3\>，以及 \<meta\> 標籤。  
4. **Insight Aggregator**: 彙整資料，計算平均字數、標題出現頻率。

## **3\. 技術組件清單 (Technology Stack)**

### **後端技術棧**

| 類別 | 建議技術 | 說明 |
| :---- | :---- | :---- |
| **語言** | Python 3.11+ | AI 與爬蟲的最佳生態系 |
| **API 框架** | FastAPI 0.104+ | 高效處理異步任務與自動 OpenAPI 文件 |
| **搜尋服務** | Google Custom Search API | 獲取 SERP 數據 (首選) |
| **網頁爬蟲** | httpx + BeautifulSoup4 | 比 requests 更快的異步抓取方案 |
| **AI 模型** | OpenAI GPT-4o-mini | 用於分析結構 (高 CP 值) |
| **資料庫** | PostgreSQL 15+ | 生產環境推薦，支援 JSON 欄位 |
| **ORM** | SQLAlchemy 2.0 | 強類型與異步支援 |
| **快取層** | Redis 7+ | 搜尋結果快取與任務佇列 |
| **任務佇列** | Celery + Redis | 處理長時間爬蟲任務 |
| **認證** | JWT (python-jose) | 無狀態身份驗證 |
| **環境管理** | Poetry / uv | 現代化依賴管理工具 |

### **前端技術棧 (Option 3: 專業版)**

| 類別 | 建議技術 | 說明 |
| :---- | :---- | :---- |
| **框架** | React 18+ | 主流生態系與豐富組件庫 |
| **語言** | TypeScript 5+ | 類型安全與更好的開發體驗 |
| **構建工具** | Vite 5+ | 極速熱更新與優化打包 |
| **狀態管理** | Zustand / TanStack Query | 輕量級狀態管理 + 服務器狀態 |
| **UI 組件庫** | shadcn/ui + Tailwind CSS | 可客製化高品質組件 |
| **表單驗證** | React Hook Form + Zod | 高效能表單與 schema 驗證 |
| **路由** | React Router v6 | 宣告式路由管理 |
| **API 通訊** | Axios / Fetch API | RESTful API 呼叫 |
| **Markdown 編輯器** | TipTap / Monaco Editor | 富文本編輯與即時預覽 |
| **圖表視覺化** | Recharts / Chart.js | SEO 數據視覺化 |

## **4\. 資料模型設計 (Data Schema)**

為了方便調整，建議定義清晰的資料結構：

### **A. 搜尋結果物件 (SearchResult)**

{  
  "rank": 1,  
  "title": "如何在家做義大利麵",  
  "url": "\[https://example.com/pasta\](https://example.com/pasta)",  
  "snippet": "本文介紹三種最受歡迎的義大利麵做法...",  
  "scraped\_at": "2026-01-07T12:00:00Z"  
}

### **B. 競品分析報告 (AnalysisReport)**

{  
  "keyword": "義大利麵做法",  
  "avg\_word\_count": 2450,  
  "common\_h2\_tags": \["必備材料", "烹飪步驟", "常見問題"\],  
  "competitor\_data": \[ ...list of SearchResult with structures... \]  
}

## **3.5\. 前後端架構設計 (Frontend-Backend Architecture)**

本系統採用 **前後端分離架構**，通過 RESTful API 進行通訊。

### **A. 整體架構圖**

```
┌─────────────────────────────────────────────────────────────┐
│                      使用者瀏覽器                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  React SPA (TypeScript)                              │  │
│  │  - 關鍵字研究介面                                     │  │
│  │  - 競品分析儀表板                                     │  │
│  │  - 文章編輯器 (Markdown)                             │  │
│  │  - 專案管理                                          │  │
│  └───────────────────┬──────────────────────────────────┘  │
└────────────────────────┼────────────────────────────────────┘
                         │ HTTPS (JWT Token)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Nginx (反向代理 + SSL 終止)                    │
└───────────┬─────────────────────────┬───────────────────────┘
            │                         │
            ▼                         ▼
┌───────────────────────┐   ┌─────────────────────────────────┐
│  FastAPI 應用服務器    │   │  Celery Worker (背景任務)       │
│  - RESTful API        │   │  - 異步網頁爬取                 │
│  - WebSocket (可選)    │   │  - 批量內容生成                 │
│  - 用戶認證           │   │  - 定時更新 SERP                │
└───────┬───────────────┘   └────────┬────────────────────────┘
        │                            │
        ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   資料與快取層                               │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  PostgreSQL      │  │  Redis            │                │
│  │  - 用戶資料       │  │  - SERP 快取      │                │
│  │  - 專案資料       │  │  - 任務佇列       │                │
│  │  - 文章版本       │  │  - Session 儲存   │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### **B. 後端架構 (FastAPI)**

```
backend/
├── app/
│   ├── main.py                    # FastAPI 應用入口
│   ├── config.py                  # 環境變數配置
│   │
│   ├── api/                       # API 路由層
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # 登入/註冊/JWT
│   │   │   ├── research.py       # 關鍵字研究端點
│   │   │   ├── content.py        # 內容生成端點
│   │   │   ├── projects.py       # 專案管理
│   │   │   └── webhooks.py       # 第三方整合
│   │   └── dependencies.py        # 全域依賴注入
│   │
│   ├── core/                      # 核心邏輯層
│   │   ├── security.py           # JWT/密碼加密
│   │   ├── rate_limiter.py       # API 限流器
│   │   └── exceptions.py         # 自定義異常
│   │
│   ├── services/                  # 業務邏輯層
│   │   ├── serp_service.py       # Google Search 封裝
│   │   ├── crawler_service.py    # 網頁爬蟲邏輯
│   │   ├── llm_service.py        # OpenAI API 封裝
│   │   ├── analysis_service.py   # 競品分析邏輯
│   │   └── content_service.py    # 文章生成流程
│   │
│   ├── models/                    # SQLAlchemy Models
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── article.py
│   │   └── search_cache.py
│   │
│   ├── schemas/                   # Pydantic Schemas
│   │   ├── user.py               # UserCreate, UserResponse
│   │   ├── research.py           # ResearchRequest, ResearchResult
│   │   └── content.py            # ContentGenerateRequest
│   │
│   ├── tasks/                     # Celery 背景任務
│   │   ├── crawler_tasks.py      # 批量爬蟲任務
│   │   └── content_tasks.py      # 批量生成任務
│   │
│   └── utils/                     # 工具函數
│       ├── html_parser.py        # HTML 結構提取
│       ├── seo_analyzer.py       # SEO 指標計算
│       └── cache_manager.py      # Redis 快取邏輯
│
├── tests/                         # 測試目錄
├── alembic/                       # 資料庫遷移
├── pyproject.toml                 # Poetry 配置
└── Dockerfile                     # 容器化部署
```

### **C. 前端架構 (React + TypeScript)**

```
frontend/
├── src/
│   ├── main.tsx                   # 應用入口
│   ├── App.tsx                    # 根組件
│   │
│   ├── pages/                     # 頁面組件
│   │   ├── Dashboard.tsx         # 儀表板首頁
│   │   ├── Research.tsx          # 關鍵字研究頁
│   │   ├── ContentEditor.tsx     # 文章編輯器
│   │   ├── Projects.tsx          # 專案列表
│   │   ├── Login.tsx             # 登入頁
│   │   └── Settings.tsx          # 設定頁
│   │
│   ├── components/                # 可重用組件
│   │   ├── ui/                   # shadcn/ui 組件
│   │   ├── KeywordInput.tsx      # 關鍵字輸入框
│   │   ├── CompetitorCard.tsx    # 競品資訊卡片
│   │   ├── SEOMetrics.tsx        # SEO 指標視覺化
│   │   ├── MarkdownEditor.tsx    # 編輯器組件
│   │   └── LoadingSpinner.tsx    # 載入動畫
│   │
│   ├── hooks/                     # 自定義 Hooks
│   │   ├── useAuth.ts            # 認證狀態管理
│   │   ├── useResearch.ts        # 研究資料獲取
│   │   └── useDebounce.ts        # 防抖處理
│   │
│   ├── services/                  # API 呼叫層
│   │   ├── api.ts                # Axios 實例配置
│   │   ├── auth.service.ts       # 認證 API
│   │   ├── research.service.ts   # 研究 API
│   │   └── content.service.ts    # 內容 API
│   │
│   ├── store/                     # 狀態管理
│   │   ├── authStore.ts          # 用戶認證狀態
│   │   ├── projectStore.ts       # 專案狀態
│   │   └── uiStore.ts            # UI 控制狀態
│   │
│   ├── types/                     # TypeScript 類型定義
│   │   ├── api.types.ts          # API 回應類型
│   │   ├── research.types.ts     # 研究相關類型
│   │   └── content.types.ts      # 內容相關類型
│   │
│   ├── utils/                     # 工具函數
│   │   ├── formatters.ts         # 資料格式化
│   │   ├── validators.ts         # 表單驗證
│   │   └── seoHelpers.ts         # SEO 計算工具
│   │
│   └── styles/                    # 全域樣式
│       └── globals.css           # Tailwind + 自定義樣式
│
├── public/                        # 靜態資源
├── index.html                     # HTML 模板
├── vite.config.ts                 # Vite 配置
├── tsconfig.json                  # TypeScript 配置
├── tailwind.config.js             # Tailwind 配置
└── package.json                   # NPM 依賴
```

### **D. API 端點設計 (RESTful)**

#### **認證相關**
```
POST   /api/v1/auth/register      # 註冊
POST   /api/v1/auth/login         # 登入
POST   /api/v1/auth/refresh       # 刷新 Token
GET    /api/v1/auth/me            # 獲取當前用戶
```

#### **研究功能**
```
POST   /api/v1/research/keyword                # 提交關鍵字研究
GET    /api/v1/research/{task_id}              # 獲取研究結果
GET    /api/v1/research/{task_id}/competitors  # 獲取競品詳細資料
POST   /api/v1/research/{task_id}/export       # 匯出為 JSON/CSV
```

#### **內容生成**
```
POST   /api/v1/content/outline                 # 生成文章大綱
POST   /api/v1/content/generate                # 生成完整文章
PATCH  /api/v1/content/{article_id}            # 更新文章
GET    /api/v1/content/{article_id}/versions   # 獲取版本歷史
```

#### **專案管理**
```
GET    /api/v1/projects                        # 獲取專案列表
POST   /api/v1/projects                        # 建立新專案
GET    /api/v1/projects/{id}                   # 獲取專案詳情
DELETE /api/v1/projects/{id}                   # 刪除專案
```

#### **快取管理**
```
DELETE /api/v1/cache/keyword/{keyword}         # 清除特定關鍵字快取
DELETE /api/v1/cache/all                       # 清除所有快取
GET    /api/v1/cache/stats                     # 快取統計資訊
```

### **E. 資料流範例：關鍵字研究流程**

```
1. 用戶在前端輸入關鍵字 "義大利麵做法"
   ↓
2. React 呼叫: POST /api/v1/research/keyword
   Body: { "keyword": "義大利麵做法", "market": "tw" }
   ↓
3. FastAPI 檢查 Redis 快取
   - 若命中 → 直接返回快取結果
   - 若未命中 → 觸發 Celery 任務
   ↓
4. Celery Worker 執行:
   a. 呼叫 Google Custom Search API
   b. 異步爬取前 10 名網址
   c. 提取標題結構、字數、關鍵字
   d. 儲存至 PostgreSQL
   e. 快取至 Redis (7 天過期)
   ↓
5. 前端透過輪詢或 WebSocket 獲取結果
   GET /api/v1/research/{task_id}
   ↓
6. 顯示競品分析儀表板
   - 平均字數圖表
   - 常見標題結構
   - 關鍵字密度分析
```

### **F. 安全性設計**

| 安全需求 | 實作方案 |
|---------|---------|
| **API 認證** | JWT Token (15 分鐘過期) + Refresh Token (7 天) |
| **密碼儲存** | bcrypt 加密 (10 rounds) |
| **HTTPS 強制** | Nginx SSL 終止 + HSTS Header |
| **CORS 控制** | 僅允許前端域名 |
| **API 限流** | 每用戶 100 請求/小時 (Redis 計數器) |
| **SQL 注入防護** | SQLAlchemy ORM 參數化查詢 |
| **XSS 防護** | React 自動轉義 + CSP Header |
| **敏感資料** | 環境變數 (.env) + Secrets Manager |

### **G. 部署架構 (Docker Compose)**

```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
  
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/seo_db
      - REDIS_URL=redis://redis:6379
    depends_on: [db, redis]
  
  celery_worker:
    build: ./backend
    command: celery -A app.tasks worker -l info
    depends_on: [redis, db]
  
  frontend:
    build: ./frontend
    environment:
      - VITE_API_URL=https://api.yourdomain.com
  
  db:
    image: postgres:15-alpine
    volumes: ["postgres_data:/var/lib/postgresql/data"]
  
  redis:
    image: redis:7-alpine
    volumes: ["redis_data:/data"]
```

### **H. 開發工作流程**

1. **本地開發**
   - 後端: `poetry run uvicorn app.main:app --reload`
   - 前端: `npm run dev`
   - Celery: `celery -A app.tasks worker`

2. **Git 分支策略**
   - `main`: 生產環境
   - `develop`: 開發環境
   - `feature/*`: 功能分支

3. **CI/CD 流程**
   - GitHub Actions 自動測試
   - Docker 映像自動構建
   - 自動部署至 Staging 環境


## **5\. 開發分階段時程 (Development Roadmap)**

### **Phase 1: 後端核心 (2-3 週)**
- ✅ FastAPI 專案架構建立
- ✅ PostgreSQL + SQLAlchemy 資料模型
- ✅ Google Search API 整合
- ✅ 網頁爬蟲服務 (httpx + BeautifulSoup)
- ✅ JWT 認證系統
- ✅ Redis 快取層

### **Phase 2: 前端基礎 (2 週)**
- ✅ React + Vite 專案初始化
- ✅ Tailwind CSS + shadcn/ui 設定
- ✅ 登入/註冊頁面
- ✅ 關鍵字研究介面
- ✅ API 整合與狀態管理

### **Phase 3: 核心功能整合 (2-3 週)**
- ✅ Celery 背景任務系統
- ✅ 競品分析儀表板 (圖表視覺化)
- ✅ OpenAI API 整合 (大綱生成)
- ✅ Markdown 編輯器整合
- ✅ 專案管理功能

### **Phase 4: 進階功能 (2 週)**
- ✅ WebSocket 即時進度推送
- ✅ SEO 分數檢查器
- ✅ 批量內容生成
- ✅ 資料匯出功能 (CSV/JSON)

### **Phase 5: 優化與部署 (1-2 週)**
- ✅ 單元測試與整合測試
- ✅ Docker Compose 容器化
- ✅ Nginx 反向代理設定
- ✅ CI/CD Pipeline 建立
- ✅ 監控與日誌系統 (Sentry/ELK)

**總開發時間**: 約 9-12 週 (2-3 個月)

## **6\. 擴充性設計考量 (Future-Proofing)**

* **適配器模式 (Adapter Pattern)**: 將搜尋邏輯封裝在 Interface 中。未來如果 Google API 太貴，可以輕鬆更換為 Bing 或 DuckDuckGo。  
* **動態爬蟲開關**: 若遇到 React/Vue 等 JavaScript 渲染的網站，系統應能自動切換至 Playwright (無頭瀏覽器)。