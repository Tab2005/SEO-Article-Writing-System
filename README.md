# SEO-Article-Writing-System

## 開發環境快速啟動 🚀

以下為快速在本地啟動專案的步驟（含虛擬環境、Poetry、以及本地啟動指令）。

### 先決條件

- Python 3.11+
- Node.js 18+（或符合前端專案需求之版本）
- Git
- Poetry（用於 Python 相依管理）

### 1) 取得原始碼

```bash
git clone https://github.com/Tab2005/SEO-Article-Writing-System.git
cd SEO-Article-Writing-System
```

### 2) 後端（使用 Poetry 管理 Python 相依）

```bash
# 安裝相依
poetry install

# 建立或啟動虛擬環境（選用）
poetry shell

# 設定環境變數（請建立 .env 或複製範例）
cp .env.example .env
# 編輯 .env 填入 DATABASE_URL, REDIS_URL, OPENAI_API_KEY 等

# 啟動後端開發伺服器
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) 前端（React + Vite）

```bash
cd frontend
npm install
npm run dev
# 預設會在 http://localhost:5173
```

### 4) 背景任務 (Celery)

```bash
# 需確認 REDIS_URL 已設定
poetry run celery -A app.tasks worker -l info
```

### 5) 使用 Docker（可選）

```bash
# 使用 Docker Compose 啟動所有服務
docker compose up --build
```

### 6) 常用指令

- 執行測試：`poetry run pytest`
- 格式化程式：`poetry run ruff format` 或 `prettier`（前端）
- 建立資料庫遷移：`alembic revision --autogenerate -m "msg"` / `alembic upgrade head`

> 如需我幫您建立 `.env.example`、CI workflow 或 Docker Compose 範例，我可以接著幫您完成。

---

## 系統結構設計文件 (SSD)

以下為原始設計文件 `SEO 文章撰寫系統.md` 的內容重點（完整文件亦包含於專案）：

# **SEO 文章撰寫系統：系統結構設計文件 (SSD)**

## **1. 系統架構概覽 (Architecture Overview)**

本系統採用 **模組化架構**，確保研究、分析、撰寫與儲存四個核心功能解耦。

### **核心模組圖解**

1. **用戶介面 (UI Layer)**: 接收關鍵字輸入，顯示研究報告與生成文章。
2. **研究模組 (Research Engine)**: 負責搜尋結果抓取與網頁內容爬取。
3. **分析模組 (Analysis Engine)**: 提取關鍵字、標題結構、字數統計。
4. **內容生成模組 (Content Generator)**: 串接 LLM (GPT-4o/Gemini) 生成大綱與內文。
5. **儲存與快取層 (Data & Cache)**: 儲存搜尋結果以節省 API 費用。

## **2. 階段 1：研究與競品分析流程 (Detailed Data Flow)**

這是目前開發的重點區塊，資料流向如下：

1. **Keyword Input**: 用戶輸入目標關鍵字。
2. **SERP Fetcher**: 呼叫 Google Custom Search API。
   * *Input*: Keyword, API Key, CX ID。
   * *Output*: List of Objects (Title, Link, Snippet)。
3. **Content Crawler**: 對前 10 名網址進行異步爬取。
   * *Logic*: 提取 <h1> 到 <h3>，以及 <meta> 標籤。
4. **Insight Aggregator**: 彙整資料，計算平均字數、標題出現頻率。

## **3. 技術組件清單 (Technology Stack)**

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

## **4. 資料模型設計 (Data Schema)**

為了方便調整，建議定義清晰的資料結構：

### **A. 搜尋結果物件 (SearchResult)**

{  
  "rank": 1,  
  "title": "如何在家做義大利麵",  
  "url": "[https://example.com/pasta](https://example.com/pasta)",  
  "snippet": "本文介紹三種最受歡迎的義大利麵做法...",  
  "scraped_at": "2026-01-07T12:00:00Z"  
}

### **B. 競品分析報告 (AnalysisReport)**

{  
  "keyword": "義大利麵做法",  
  "avg_word_count": 2450,  
  "common_h2_tags": ["必備材料", "烹飪步驟", "常見問題"],  
  "competitor_data": [ ...list of SearchResult with structures... ]  
}

## **3.5. 前後端架構設計 (Frontend-Backend Architecture)**

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
... (file continues)