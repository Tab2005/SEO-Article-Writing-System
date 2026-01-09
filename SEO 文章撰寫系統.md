# **SEO 文章撰寫系統：系統結構設計文件 (SSD)**

## **1\. 系統架構概覽 (Architecture Overview)**

本系統採用 **模組化架構**，確保研究、分析、撰寫與儲存四個核心功能解耦。

### **核心模組圖解**

1. **用戶介面 (UI Layer)**: 接收關鍵字輸入，顯示研究報告與生成文章。  
2. **研究模組 (Research Engine)**: 負責搜尋結果抓取與網頁內容爬取。  
3. **分析模組 (Analysis Engine)**: 提取關鍵字、標題結構、字數統計。  
4. **內容生成模組 (Content Generator)**: 串接 LLM (GPT-4o/Gemini) 生成大綱與內文。  
5. **儲存與快取層 (Data & Cache)**: 儲存搜尋結果以節省 API 費用。

## **2\. 技術組件清單 (Technology Stack)**

### **後端技術棧 ✅ 已實現**

| 類別 | 技術 | 狀態 |
|------|------|------|
| **語言** | Python 3.11+ | ✅ |
| **API 框架** | FastAPI 0.104+ | ✅ |
| **搜尋服務** | Google Custom Search API | ✅ |
| **網頁爬蟲** | httpx + BeautifulSoup4 | ✅ |
| **AI 模型** | OpenAI GPT-4o-mini | ✅ |
| **資料庫** | PostgreSQL 15+ | ✅ |
| **ORM** | SQLAlchemy 2.0 (async) | ✅ |
| **快取層** | Redis 7+ | ✅ |
| **任務佇列** | Celery + Redis | ✅ |
| **認證** | JWT + bcrypt + Google OAuth | ✅ |

### **前端技術棧 ✅ 已實現**

| 類別 | 技術 | 狀態 |
|------|------|------|
| **框架** | React 18+ | ✅ |
| **語言** | TypeScript 5+ | ✅ |
| **構建工具** | Vite 5+ | ✅ |
| **狀態管理** | Zustand + TanStack Query | ✅ |
| **UI 樣式** | Tailwind CSS | ✅ |
| **路由** | React Router v6 | ✅ |
| **API 通訊** | Axios | ✅ |
| **認證** | @react-oauth/google | ✅ |

## **3\. 開發進度 (Development Roadmap) ✅ 全部完成**

### **Phase 1: 後端核心 ✅ COMPLETED**
- ✅ FastAPI 專案架構建立
- ✅ PostgreSQL + SQLAlchemy 資料模型
- ✅ Google Search API 整合
- ✅ 網頁爬蟲服務 (httpx + BeautifulSoup)
- ✅ JWT 認證系統
- ✅ Redis 快取層
- ✅ OpenAI API 整合

### **Phase 2: 前端基礎 ✅ COMPLETED**
- ✅ React + Vite + TypeScript 專案初始化
- ✅ Tailwind CSS 設定
- ✅ Google OAuth 登入頁面 (取代傳統註冊)
- ✅ 關鍵字研究介面
- ✅ API 整合與狀態管理

### **Phase 3: 核心功能整合 ✅ COMPLETED**
- ✅ Celery 背景任務系統
- ✅ 內容生成頁面
- ✅ 專案管理功能

### **Phase 4: 進階功能 ✅ COMPLETED**
- ✅ WebSocket 即時進度推送
- ✅ SEO 分數檢查器
- ✅ 資料匯出功能 (CSV/JSON)

### **Phase 5: 優化與部署 ✅ COMPLETED**
- ✅ Docker Compose 容器化
- ✅ 單元測試
- ✅ GitHub Actions CI/CD

**總開發進度**: 100% ✅

---

## **4\. 專案結構 (Project Structure)**

### **完整目錄結構**
```
SEO-Article-Writing-System/
├── backend/                      # FastAPI 後端
│   ├── app/
│   │   ├── main.py              # 應用入口
│   │   ├── config.py            # 環境配置
│   │   ├── api/v1/endpoints/    # API 端點
│   │   │   ├── auth.py          # 認證 (含 Google OAuth)
│   │   │   ├── research.py      # 關鍵字研究
│   │   │   ├── content.py       # 內容生成
│   │   │   ├── projects.py      # 專案管理
│   │   │   ├── seo.py           # SEO 檢查
│   │   │   └── websocket.py     # 即時推送
│   │   ├── core/
│   │   │   ├── security.py      # JWT + 密碼
│   │   │   ├── database.py      # 資料庫連線
│   │   │   ├── celery_app.py    # Celery 配置
│   │   │   └── websocket.py     # WS 管理器
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── schemas/             # Pydantic 驗證
│   │   ├── services/            # 業務邏輯
│   │   │   ├── google_search.py
│   │   │   ├── crawler_service.py
│   │   │   ├── analysis_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── cache_manager.py
│   │   │   ├── seo_checker.py
│   │   │   ├── user_service.py
│   │   │   └── google_oauth.py
│   │   ├── tasks/               # Celery 任務
│   │   └── utils/               # 工具函數
│   ├── tests/                   # 單元測試
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                     # React 前端
│   ├── src/
│   │   ├── main.tsx             # 入口 (含 GoogleOAuthProvider)
│   │   ├── App.tsx              # 路由配置
│   │   ├── pages/
│   │   │   ├── Login.tsx        # Google OAuth 登入
│   │   │   ├── Dashboard.tsx    # 儀表板
│   │   │   ├── Research.tsx     # 關鍵字研究
│   │   │   ├── ContentGeneration.tsx  # 內容生成
│   │   │   ├── SEOChecker.tsx   # SEO 檢查
│   │   │   └── Projects.tsx     # 專案管理
│   │   ├── components/
│   │   │   └── Layout.tsx       # 側邊欄佈局
│   │   ├── services/            # API 服務
│   │   ├── store/               # Zustand 狀態
│   │   ├── hooks/               # React Query hooks
│   │   └── types/               # TypeScript 類型
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── docker-compose.yml            # 容器編排
├── .github/workflows/ci.yml      # CI/CD
└── README.md
```

---

## **5\. API 端點設計**

### **認證 (含 Google OAuth)**
```
POST   /api/v1/auth/register      # 註冊 (email/password)
POST   /api/v1/auth/login         # 登入
POST   /api/v1/auth/google        # Google OAuth 登入 ✨
POST   /api/v1/auth/logout        # 登出 (令牌黑名單)
POST   /api/v1/auth/refresh       # 刷新 Token
GET    /api/v1/auth/me            # 獲取當前用戶
PATCH  /api/v1/auth/me            # 更新個人資料
POST   /api/v1/auth/change-password  # 密碼變更
```

### **研究功能**
```
GET    /api/v1/research/serp      # 直接獲取 SERP 結果
GET    /api/v1/research/analyze   # 完整關鍵字分析
POST   /api/v1/research/keyword   # 提交異步研究任務
GET    /api/v1/research/{task_id} # 獲取任務狀態
```

### **內容生成**
```
POST   /api/v1/content/outline    # 生成文章大綱
POST   /api/v1/content/generate   # 生成完整文章
POST   /api/v1/content/optimize   # SEO 優化內容
```

### **SEO 檢查**
```
POST   /api/v1/seo/analyze        # SEO 分數分析
POST   /api/v1/seo/export/json    # 匯出 JSON 報告
```

### **WebSocket**
```
WS     /api/v1/ws?token=<jwt>     # 即時進度推送
```

---

## **6\. 快速開始**

### **開發環境**
```bash
# 後端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

### **Docker 部署**
```bash
# 啟動所有服務
docker-compose up -d

# 查看狀態
docker-compose ps

# 查看日誌
docker-compose logs -f backend
```

### **環境變數配置**

**後端 `.env`:**
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/seo_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CX_ID=your-cx-id
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-secret
OPENAI_API_KEY=your-openai-key
```

**前端 `.env.local`:**
```env
VITE_GOOGLE_CLIENT_ID=your-oauth-client-id
```

---

## **7\. 系統功能一覽**

| 功能 | 描述 | 狀態 |
|------|------|------|
| **Google OAuth 登入** | 一鍵 Google 帳號登入 | ✅ |
| **關鍵字研究** | SERP 分析 + 競品爬取 | ✅ |
| **AI 內容生成** | GPT-4o 大綱 + 文章生成 | ✅ |
| **SEO 分數檢查** | 標題、密度、結構分析 | ✅ |
| **專案管理** | 多專案文章管理 | ✅ |
| **即時進度** | WebSocket 任務追蹤 | ✅ |
| **資料匯出** | CSV/JSON 格式匯出 | ✅ |
| **Docker 部署** | 一鍵容器化部署 | ✅ |
| **CI/CD** | GitHub Actions 自動化 | ✅ |

---

**最後更新**: 2026/01/09  
**系統版本**: v1.0.0  
**開發進度**: 100% ✅ 全部完成