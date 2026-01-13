# Seonize UX Prototype → 現有專案導入建議（2026-01-12）

> 目標：把 [Seonize UI/UX Prototype.md](../Seonize%20UI/UX%20Prototype.md) 的「4 步驟策略導引」體驗融入目前專案（FastAPI + React/Vite），並以最小風險方式逐步產品化。

---

## 1. UX Prototype 的核心工作流（你要導入的體驗）

Prototype 是一個 **Strategy Wizard**：

1) **Step 1：競品分析啟動**
- 輸入目標關鍵字 → 掃描前 10 名競品 → 產出研究報告

2) **Step 2：策略選擇（最關鍵）**
- Intent（資訊/商業/交易/導航）
- Tone/Style（語氣風格）
- LSI（語意關鍵字）可選取，影響章節數量
- H1 標題挑選
- 「應用策略並重產標題」
- 額外：E-E-A-T 專家提示、AI 建議標籤

3) **Step 3：動態大綱（可編輯）**
- 由選擇的 LSI 動態生成章節
- 可返回 Step2 調整策略
- 大綱可拖曳/新增章節（prototype UI 有，但邏輯可先簡化）

4) **Step 4：撰寫進度 + 預覽**
- 逐段生成/進度條/右側預覽

---

## 2. 與現有系統的功能映射（已具備 vs 缺口）

### 2.1 Step 1（Research）
**現有已具備：**
- 前端研究頁（任務制、歷史、輪詢）：[frontend/src/pages/Research.tsx](../frontend/src/pages/Research.tsx)
- research service：建立任務、取 report：[frontend/src/services/research.service.ts](../frontend/src/services/research.service.ts)

**建議導入方式：**
- Wizard Step1 直接呼叫 `researchService.createJob()`，用輪詢拿到 report 作為 Step2 策略資料來源。

### 2.2 Step 2（策略：Intent/Tone/LSI/H1/重產標題）
**現有可用資料來源：**
- Research report 內的 TF-IDF / keyword 分析（前端型別已有 `tfidf_analysis`）

**目前缺口（需要補齊）：**
- `aiDetectedIntent`（偵測/建議意圖）
- `suggestedTitles[]`（可依 intent/tone 變化、可「重產」）
- `lsiKeywords[]` 權重/預選規則（prototype 有 weight + essential）
- `eeatTips[]`（E-E-A-T 提示）

**建議：**
- LSI 候選：由 `tfidf_analysis.suggested_keywords` + 類別（high_frequency/semantic_related/long_tail）組合
- Intent/Titles/E-E-A-T：用 LLM 產生「策略包（Strategy Pack）」

### 2.3 Step 3（動態大綱編輯器）
**現有已具備：**
- 大綱生成 + 可編輯（拖曳、增刪、改標題）：[frontend/src/pages/ContentGeneration.tsx](../frontend/src/pages/ContentGeneration.tsx)
- 生成大綱 API：`POST /api/v1/content/outline`

**建議：**
- 把 Step2 的 `selected_lsi / intent / tone / selected_title` 作為「提示條件」餵給 `/content/outline`，讓章節更貼合策略。

### 2.4 Step 4（撰寫進度 + 預覽）
**現有已具備：**
- 一次性生成全文：`POST /api/v1/content/generate`

**缺口：**
- 串流（SSE/WS）或逐段生成進度

**建議導入節奏：**
- MVP 先用「假進度條」包裝一次性生成
- 產品化再做 SSE 串流（體驗接近 prototype）

---

## 3. 三種導入方案（由快到完整）

### 方案 A：前端 Wizard 編排（最快上線 / 最小後端改動）
**內容：**
- 新增 Wizard 頁面，把 Research → 策略 → 大綱 → 生成串成 1 條 UI 流程
- LSI 直接由 TF-IDF 組出候選 + 預選
- Intent/Titles/E-E-A-T 先用既有 AI endpoint 產 JSON（或暫時前端模板）
- Step4 用假進度條 + 一次性生成全文

**優點：**最快落地、風險低

**缺點：**策略邏輯分散在前端，未來要做可重跑/可儲存會比較難

### 方案 B：新增後端 Strategy Pack API（推薦）
**內容：**
- 新增 `/api/v1/content/strategy`（或 `/api/v1/strategy`）
- 輸入 keyword/market/depth 或 job_id
- 輸出完整策略包（intent/tone/title/lsi/eeat）
- 「重產標題」= 同 endpoint 帶不同 intent/tone 再打一次

**優點：**可重用、可測試、前端更乾淨

**缺點：**需要後端 schema + endpoint 開發

### 方案 C：產品化（持久化 + 串流 + 版本）
**內容：**
- Strategy/Outline/Content 全部落 DB（Article draft）
- 支援中斷續做、回滾、版本比較
- Step4 用 SSE/WS 串流生成

**優點：**完整產品體驗與可追溯性

**缺點：**開發成本最高

---

## 4. 建議的落地順序（務實路線）

### Phase 1（MVP）：先把體驗串起來（建議 1–3 天）
- [ ] 新增「策略導引」Wizard 頁面（獨立 route）
- [ ] Step1：research job → report
- [ ] Step2：用 report 的 TF-IDF 組 LSI 候選 + 預選；LLM 產出 intent/title/eeat（先走既有 AI endpoint）
- [ ] Step3：重用現有大綱編輯 UI（把策略狀態帶入）
- [ ] Step4：假進度條 + 呼叫 `/content/generate` 一次拿全文

### Phase 2（推薦）：把策略抽成後端 Strategy Pack（建議 3–7 天）
- [ ] 新增 Strategy Pack endpoint + schema
- [ ] 前端 Wizard 改為「只負責 UI/狀態」，策略全部由後端統一產出
- [ ] `/content/outline` 支援 `intent/tone/selected_lsi/selected_title`（可選）

### Phase 3（產品化）：持久化 + 串流（1–3 週）
- [ ] Article draft 儲存策略、outline、content、status
- [ ] SSE/WS 串流生成，進度與分段預覽

---

## 5. Strategy Pack（建議資料契約草案）

> 這份契約的目的：讓前端能 1:1 做出 prototype Step2，並支援「重產標題」。

**Request（建議）**
- keyword, market, depth
- （可選）job_id：有就重用 research 結果
- intent（可選）：使用者指定時覆蓋
- tone（可選）

**Response（建議）**
- ai_detected_intent
- suggested_intents[]（含理由/置信度）
- suggested_tones[]
- suggested_titles[]
- lsi_keywords[]：[{ term, weight, essential, source }]
- eeat_tips[]
- references：例如使用了哪些 competitor signals / tf-idf

---

## 6. UI/元件拆分建議（方便逐步導入）

（先不追求一次做完，拆成可獨立完成的小塊）

- WizardLayout：上方 Stepper + 底部固定 CTA bar
- Step1ResearchPanel：keyword/market/depth + 任務狀態
- Step2StrategyPanel：
  - IntentPicker
  - TonePicker
  - LsiChips（可選取/顯示 weight）
  - TitlePicker（點選 H1）
  - RegenerateTitlesButton
  - EeatTipsCard
- Step3OutlineEditor：直接重用現有 ContentGeneration 的 outline editing（或抽成共用 component）
- Step4WritingPreview：假進度（MVP）→ SSE 串流（進階）

---

## 7. 驗收標準（MVP 應該要做到的）

- 能從 Wizard 完整跑完一次：keyword → research → 策略 → 大綱 → 生成文章
- Step2 能切 intent/tone 並「重產標題」
- Step2 的 LSI 選取會影響 Step3 章節（至少在 prompt / 章節數量上有可見差異）
- Step3 可改標題/順序，能成功生成全文

---

## 8. 下一步建議（你可以從這裡挑一個開始）

1) 先做 Phase 1：新增一個 Wizard 頁面，把流程串起來
2) 或先做 Phase 2：先定 Strategy Pack API contract，後端先做好，再做前端

如果你決定從 Phase 1 開始，我可以直接幫你在前端新增 Wizard 頁（不破壞現有 Research/ContentGeneration），先做一條可跑通的流程。