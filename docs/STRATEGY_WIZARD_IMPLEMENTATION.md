# Strategy Wizard MVP 實作計畫

> 建立日期：2026-01-13
> 狀態：進行中

新增一個獨立的「策略導引 Wizard」頁面（方案 A），實現 UX Prototype 的 4 步驟流程，重用現有 Research 和 ContentGeneration 的服務與邏輯。

---

## 目標

把 [UX Prototype.md](../Seonize%20UI/UX%20Prototype.md) 的「4 步驟策略導引」體驗串成一條可跑通的前端流程。

---

## Proposed Changes

### Frontend 路由與導航

#### [MODIFY] App.tsx
- 新增 `import StrategyWizard from './pages/StrategyWizard'`
- 新增路由 `<Route path="strategy-wizard" element={<StrategyWizard />} />`

#### [MODIFY] Layout.tsx
- 在 `navItems` 陣列新增：`{ path: '/strategy-wizard', icon: Sparkles, label: '策略導引' }`

---

### 新增頁面與元件

#### [NEW] StrategyWizard.tsx

主要 Wizard 頁面，包含以下功能：

**Step 1: 競品分析啟動**
- 關鍵字輸入欄位
- 呼叫 `researchService.createJob()` 建立任務
- 輪詢 `researchService.getJob()` 取得狀態
- 完成後呼叫 `researchService.getJobReport()` 取得報告

**Step 2: 策略選擇（核心功能）**
- IntentPicker：4 種意圖選項（資訊/商業/交易/導航）
- TonePicker：6 種風格選項
- LsiChips：從 `report.tfidf_analysis.suggested_keywords` 組合 LSI 候選
- TitlePicker：顯示建議標題（暫用模板生成，未來接 LLM）
- 「應用策略並重產標題」按鈕

**Step 3: 動態大綱**
- 根據選取的 LSI 動態生成章節
- 呼叫 `contentService.generateOutline()` 時帶入策略參數
- 支援編輯標題、拖曳排序、新增/刪除章節
- 「返回修改策略」按鈕

**Step 4: 撰寫進度與預覽**
- 假進度條 UI（MVP 先不做 SSE 串流）
- 呼叫 `contentService.generateContent()` 生成全文
- 右側預覽面板顯示結果

---

## 資料流設計

```
Step 1: 輸入關鍵字 
    ↓
createJob() + 輪詢 getJob()
    ↓
getJobReport() 取得報告
    ↓
Step 2: 策略選擇（從報告取 TF-IDF 作為 LSI 候選）
    ↓
Step 3: generateOutline() 生成大綱
    ↓
Step 4: generateContent() 生成全文
    ↓
預覽結果
```

### LSI 候選來源
- `report.tfidf_analysis.suggested_keywords`（高分關鍵詞）
- `report.tfidf_analysis.keyword_categories.semantic_related`（語意相關）

---

## UI 元件拆分

| 元件 | 功能 |
|------|------|
| `WizardStepper` | 頂部 4 步驟進度指示器 |
| `Step1ResearchPanel` | 關鍵字輸入 + 任務狀態 |
| `Step2StrategyPanel` | Intent/Tone/LSI/Title 選擇器 |
| `Step3OutlineEditor` | 動態大綱編輯器 |
| `Step4WritingPreview` | 進度條 + 全文預覽 |

> **Note**: MVP 階段先將所有元件寫在 `StrategyWizard.tsx` 內，驗證流程後再視需要拆分。

---

## Verification Plan

### Manual Verification

1. **啟動前後端**
2. **驗證路由與導航**：確認側邊欄出現「策略導引」選項
3. **驗證 Step 1**：輸入關鍵字並確認任務狀態變化
4. **驗證 Step 2**：確認 Intent/Tone/LSI/Title 選擇器功能
5. **驗證 Step 3**：確認大綱動態生成與編輯功能
6. **驗證 Step 4**：確認進度條與全文預覽

### 驗收標準
- [ ] 能從 Wizard 完整跑完一次：keyword → research → 策略 → 大綱 → 生成文章
- [ ] Step 2 能切 intent/tone 並「重產標題」
- [ ] Step 2 的 LSI 選取會影響 Step 3 章節數量
- [ ] Step 3 可改標題/順序，能成功生成全文

---

## 實作進度

- [x] 路由與導航設定
- [x] StrategyWizard.tsx 頁面建立
- [x] Step 1 競品分析面板
- [x] Step 2 策略選擇面板
- [x] Step 3 動態大綱編輯
- [x] Step 4 撰寫預覽
- [x] Phase 1 MVP 驗證完成

---

## Phase 2：Strategy Pack API（後端）

### 目標
將前端的策略邏輯移到後端，提供統一的 `/api/v1/content/strategy` endpoint。

### 新增檔案

#### [NEW] strategy_service.py
- 位置：`backend/app/services/strategy_service.py`
- 功能：整合 TF-IDF、LLM 產生完整策略包
- 方法：`generate_strategy_pack(keyword, market, job_id, intent, tone)`

### 修改檔案

#### [MODIFY] content.py
- 位置：`backend/app/api/v1/endpoints/content.py`
- 新增：`POST /strategy` endpoint
- 新增：`StrategyRequest` 和 `StrategyResponse` schema

#### [MODIFY] StrategyWizard.tsx
- 改為呼叫 `/api/v1/content/strategy` 取得策略包
- Step 2 的 LSI/Intent/Titles 改由後端統一產生

### API 契約

**Request**
```json
{
  "keyword": "減脂方法",
  "market": "tw",
  "job_id": "uuid (optional)",
  "intent": "informational (optional)",
  "tone": "專業教育風 (optional)"
}
```

**Response**
```json
{
  "ai_detected_intent": "informational",
  "suggested_intents": [
    {"value": "informational", "label": "資訊型", "confidence": 0.85}
  ],
  "suggested_tones": ["專業教育風", "新手友善型"],
  "suggested_titles": [
    "想學減脂必看！2026 最新指南",
    "5 個減脂核心觀念"
  ],
  "lsi_keywords": [
    {"term": "熱量赤字", "weight": 0.98, "essential": true, "source": "tfidf"}
  ],
  "eeat_tips": [
    "加入實際測試或個人心得",
    "引用權威來源增加可信度"
  ]
}
```

### 實作順序
1. [x] 新增 `strategy_service.py`
2. [x] 新增 `POST /content/strategy` endpoint
3. [x] 新增前端 `strategy.service.ts`
4. [x] 修改 `StrategyWizard.tsx` 使用新 API

---

## Phase 3：產品化（持久化 + SSE 串流）

### 目標
1. **Draft 持久化**：在 Wizard 各步驟自動儲存草稿到 DB
2. **SSE 串流生成**：取代假進度條，實現真實逐段生成
3. **中斷續做**：支援從草稿繼續編輯

### 新增/修改檔案

#### [NEW] article_draft_service.py
- 位置：`backend/app/services/article_draft_service.py`
- 功能：管理文章草稿的 CRUD 操作
- 方法：`create_draft()`, `update_draft()`, `get_draft()`, `list_drafts()`

#### [NEW] streaming_service.py
- 位置：`backend/app/services/streaming_service.py`
- 功能：SSE 串流生成內容
- 方法：`stream_article_content()` - 逐段回傳生成內容

#### [MODIFY] content.py
- 新增 `POST /content/draft` - 建立/更新草稿
- 新增 `GET /content/draft/{draft_id}` - 取得草稿
- 新增 `GET /content/generate-stream` - SSE 串流生成

#### [MODIFY] StrategyWizard.tsx
- 各步驟完成時自動儲存草稿
- Step 4 改用 EventSource 接收 SSE 串流
- 新增「繼續編輯」功能（從草稿恢復）

### API 契約

**POST /content/draft**
```json
{
  "keyword": "減脂方法",
  "step": 2,
  "strategy": { "intent": "informational", "tone": "專業教育風", ... },
  "outline": [ ... ],
  "title": "想學減脂必看！"
}
```

**GET /content/generate-stream**
```
event: progress
data: {"section": "導言", "progress": 20}

event: content
data: {"section": "導言", "content": "# 導言\n\n..."}

event: done
data: {"total_words": 2500}
```

### 資料結構擴展

現有 `Article` model 已有 `status`, `outline`, `version` 欄位。新增：
- `strategy_config` (JSON)：儲存 intent/tone/lsi/title
- `research_job_id` (UUID)：關聯研究任務

### 實作順序
1. [x] 擴展 Article model（新增 strategy_config, research_job_id）
2. [x] 新增 `article_draft_service.py`
3. [x] 新增 draft endpoints
4. [x] 新增 `streaming_service.py`
5. [x] 新增 SSE streaming endpoint
6. [x] 新增前端 `draft.service.ts`
7. [x] 前端整合 SSE 串流至 StrategyWizard
8. [x] 資料庫 migration（alembic upgrade head）
