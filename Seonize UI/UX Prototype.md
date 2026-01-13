import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Settings, 
  CheckCircle, 
  Layout, 
  FileText, 
  ArrowRight, 
  Edit3, 
  GripVertical,
  Loader2,
  ChevronRight,
  TrendingUp,
  Target,
  RefreshCw,
  Info,
  Layers,
  Sparkles,
  MousePointer2,
  Undo2,
  Plus,
  AlertCircle,
  Lightbulb
} from 'lucide-react';

/**
 * Seonize (思優化) UI/UX 原型系統 v2.6 (修復版)
 * 修復重點：
 * 1. 補回「重新應用策略並重產標題」按鈕與相關處理邏輯。
 * 2. 保持步驟 2 的專家提示與 AI 建議標籤。
 * 3. 確保步驟 3 的動態大綱與返回功能正常運作。
 */

const App = () => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [keyword, setKeyword] = useState('');
  
  // 意圖與策略相關狀態
  const [intentData, setIntentData] = useState(null);
  const [currentIntent, setCurrentIntent] = useState('');
  const [currentStyle, setCurrentStyle] = useState('');
  
  // 策略選擇狀態 (暫存)
  const [tempSelectedTitle, setTempSelectedTitle] = useState('');
  const [selectedLSI, setSelectedLSI] = useState([]);
  
  // 最終產出狀態 (步驟 3 & 4 使用)
  const [selectedTitle, setSelectedTitle] = useState('');
  const [outline, setOutline] = useState([]);
  const [articleContent, setArticleContent] = useState('');
  const [writingProgress, setWritingProgress] = useState(0);

  const intentOptions = [
    { value: 'informational', label: '📚 資訊型', desc: '教學、指南或百科。適合解決疑惑、分享知識。' },
    { value: 'commercial', label: '💰 商業型', desc: '產品評測或對比。適合購物建議、決策參考。' },
    { value: 'transactional', label: '🛒 交易型', desc: '促成購買或服務預約。目標是直接轉單。' },
    { value: 'navigational', label: '🗺️ 導航型', desc: '指引路徑或登入入口。適合品牌官網或地點導引。' }
  ];

  const styleOptions = [
    "專業教育風", "新手友善型", "權威評論風", "強烈號召風", "親切對話風", "簡潔指令風"
  ];

  // 模擬搜尋與分析
  const handleStartResearch = () => {
    if (!keyword) return;
    setLoading(true);
    setTimeout(() => {
      const dynamicLSI = [
        { word: '熱量赤字', weight: 0.98, essential: true },
        { word: '基礎代謝率 (BMR)', weight: 0.92, essential: true },
        { word: '胰島素敏感度', weight: 0.85, essential: true },
        { word: '蛋白質攝取', weight: 0.78, essential: false },
        { word: '間歇性斷食', weight: 0.65, essential: false },
        { word: '低 GI 飲食', weight: 0.55, essential: false },
        { word: '皮質醇控制', weight: 0.42, essential: false }
      ];
      
      setIntentData({
        suggestedTitles: [
          `想學${keyword}必看！2026 最新科學指南`,
          `5 個關於${keyword}的核心觀念，讓你事半功倍`,
          `破解${keyword}常見迷思：這才是最適合大眾的策略`
        ],
        lsiKeywords: dynamicLSI,
        aiDetectedIntent: 'informational'
      });
      setSelectedLSI(dynamicLSI.filter(k => k.essential).map(k => k.word));
      setCurrentIntent('informational');
      setCurrentStyle('專業教育風');
      setLoading(false);
      setStep(2);
    }, 1500);
  };

  // 補回：根據新設定重新產出標題的邏輯
  const handleRegenerateTitles = () => {
    setLoading(true);
    setTimeout(() => {
      let newTitles = [];
      if (currentIntent === 'commercial') {
        newTitles = [
          `2026 評測：${keyword}相關產品對比指南`,
          `選購建議：${keyword}該怎麼挑？優缺點全解析`,
          `${keyword}推薦清單：適合新手的 CP 值之選`
        ];
      } else {
        newTitles = [
          `如何正確${keyword}？[${currentStyle}] 帶你深入淺出`,
          `想學${keyword}？這份指南專為${currentStyle === '新手友善型' ? '初學者' : '專業人士'}設計`,
          `2026 最新研究：關於${keyword}的關鍵技巧`
        ];
      }
      
      setIntentData(prev => ({ ...prev, suggestedTitles: newTitles }));
      setTempSelectedTitle(''); // 清除之前的選擇以防混淆
      setLoading(false);
    }, 1200);
  };

  const toggleLSI = (word) => {
    setSelectedLSI(prev => 
      prev.includes(word) ? prev.filter(w => w !== word) : [...prev, word]
    );
  };

  // 根據當前選擇動態生成大綱
  const handleConfirmStrategy = () => {
    if (!tempSelectedTitle) return;
    setSelectedTitle(tempSelectedTitle);
    setLoading(true);
    
    setTimeout(() => {
      const dynamicSections = [
        { id: 'intro', text: `導言：為什麼「${keyword}」是您今年必須掌握的關鍵？`, lsi: [], sub: ['趨勢背景', '核心價值與目標'] }
      ];

      selectedLSI.forEach((lsi, index) => {
        dynamicSections.push({
          id: `h2-${index}`,
          text: `深度解析：${lsi} 如何決定您的${keyword}成效`,
          lsi: [lsi],
          sub: [`${lsi} 的運作機制`, `針對新手的實踐技巧`, '常見優化建議']
        });
      });

      dynamicSections.push({ id: 'conclusion', text: '結語與常見問題：邁向成功的最後建議', lsi: [], sub: ['FAQ 疑難排解', '後續行動清單'] });

      setOutline(dynamicSections);
      setLoading(false);
      setStep(3);
    }, 1200);
  };

  const handleStartWriting = () => {
    setStep(4);
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setWritingProgress(progress);
      setArticleContent(prev => prev + `\n\n### [${currentStyle}] 章節生成中...\n正在根據「${currentIntent}」意圖佈局內容細節。`);
      if (progress >= 100) clearInterval(interval);
    }, 800);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans pb-24">
      <nav className="bg-white border-b px-8 py-4 sticky top-0 z-20 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-2">
          <div className="bg-blue-600 p-2 rounded-lg"><TrendingUp className="text-white w-6 h-6" /></div>
          <h1 className="text-xl font-bold tracking-tight text-blue-900">Seonize 思優化</h1>
        </div>
        <div className="flex items-center gap-4">
          {[1, 2, 3, 4].map(s => (
            <div key={s} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${step >= s ? 'bg-blue-600 text-white shadow-lg shadow-blue-200' : 'bg-slate-200 text-slate-500'}`}>{step > s ? <CheckCircle className="w-5 h-5" /> : s}</div>
              {s < 4 && <div className={`w-12 h-1 mx-2 rounded-full ${step > s ? 'bg-blue-600' : 'bg-slate-200'}`} />}
            </div>
          ))}
        </div>
      </nav>

      <main className="max-w-6xl mx-auto p-8">
        {step === 1 && (
          <div className="max-w-2xl mx-auto space-y-8 py-12">
            <div className="text-center space-y-4">
              <h2 className="text-4xl font-black text-slate-800 tracking-tight">內容策略研究控制台</h2>
              <p className="text-slate-500 text-lg">輸入您的目標關鍵字，AI 將掃描前 10 名競品並擬定排位計畫。</p>
            </div>
            <div className="bg-white p-10 rounded-3xl shadow-2xl shadow-blue-100 border border-blue-50">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">主要關鍵字</label>
                  <div className="relative">
                    <Search className="absolute left-4 top-4 text-slate-400 w-5 h-5" />
                    <input type="text" className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none text-lg" placeholder="例如：想學減脂..." value={keyword} onChange={(e) => setKeyword(e.target.value)} />
                  </div>
                </div>
                <button onClick={handleStartResearch} disabled={loading || !keyword} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-5 rounded-2xl shadow-xl flex items-center justify-center gap-2 disabled:bg-slate-300 transition-all">
                  {loading ? <Loader2 className="animate-spin" /> : <><Target className="w-5 h-5" /> 開始競品分析</>}
                </button>
              </div>
            </div>
          </div>
        )}

        {step === 2 && intentData && (
          <div className="space-y-8 animate-in fade-in slide-in-from-top-4 duration-700">
            <div className="bg-blue-50 border border-blue-100 p-4 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Sparkles className="text-blue-600 w-5 h-5" />
                <p className="text-sm text-blue-800 font-medium">策略建議已產出！我們偵測到此主題最適合以「{intentData.aiDetectedIntent === 'informational' ? '資訊型' : '商業型'}」呈現。</p>
              </div>
              <div className="flex items-center gap-2 px-3 py-1 bg-white rounded-lg border border-blue-200">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-xs font-bold text-blue-600 uppercase">AI Status: Ready</span>
              </div>
            </div>

            <div className="grid grid-cols-12 gap-8">
              <div className="col-span-4 space-y-6">
                <section className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
                  <h3 className="font-bold flex items-center gap-2 text-slate-800 border-b pb-4"><Settings className="w-5 h-5 text-blue-600" /> 文章策略核心</h3>
                  
                  <div className="space-y-3">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">搜尋意圖 (Intent)</label>
                    <div className="grid gap-2">
                      {intentOptions.map(opt => (
                        <button 
                          key={opt.value}
                          onClick={() => setCurrentIntent(opt.value)}
                          className={`text-left p-3 rounded-xl border-2 transition-all relative ${currentIntent === opt.value ? 'bg-blue-50 border-blue-600 shadow-sm' : 'bg-slate-50 border-transparent hover:border-slate-200'}`}
                        >
                          <p className={`text-sm font-bold ${currentIntent === opt.value ? 'text-blue-700' : 'text-slate-700'}`}>{opt.label}</p>
                          <p className="text-[10px] text-slate-400 mt-1 leading-tight">{opt.desc}</p>
                          {intentData.aiDetectedIntent === opt.value && (
                            <span className="absolute top-2 right-2 text-[8px] bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded font-bold uppercase">AI 建議</span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">建議風格 (Tone)</label>
                    <select 
                      className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold outline-none focus:ring-2 focus:ring-blue-500"
                      value={currentStyle}
                      onChange={(e) => setCurrentStyle(e.target.value)}
                    >
                      {styleOptions.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>

                  {/* 修復點：重新產生標題的按鈕 */}
                  <button 
                    onClick={handleRegenerateTitles}
                    disabled={loading}
                    className="w-full py-4 bg-slate-900 text-white rounded-xl text-sm font-bold flex items-center justify-center gap-2 hover:bg-black transition-all shadow-md active:scale-95"
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><RefreshCw className="w-4 h-4" /> 應用策略並重產標題</>}
                  </button>
                </section>

                <section className="bg-slate-900 p-6 rounded-2xl text-white shadow-lg">
                  <h3 className="text-sm font-bold flex items-center gap-2 mb-4 text-blue-400">
                    <Lightbulb className="w-4 h-4" /> 專家撰寫建議 (E-E-A-T)
                  </h3>
                  <div className="space-y-4">
                    <p className="text-xs text-slate-300 leading-relaxed">
                      對於關鍵字「{keyword}」，前 10 名競品皆採用了大量數據支撐。建議在撰寫時：
                    </p>
                    <ul className="text-[10px] text-slate-400 space-y-2 list-disc pl-4">
                      <li>強化「經驗 (Experience)」：加入實際測試或個人心得。</li>
                      <li>對齊「{currentIntent === 'informational' ? '教學' : '評測'}」邏輯。</li>
                      <li>使用「{currentStyle}」可以讓跳出率降低 15%。</li>
                    </ul>
                  </div>
                </section>
              </div>

              <div className="col-span-8 space-y-8">
                <section className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-bold text-slate-800 flex items-center gap-2 text-lg">
                      <Layers className="w-5 h-5 text-blue-600" /> 語意關鍵字補強 (LSI)
                    </h4>
                    <span className="text-xs text-slate-400 font-medium">已選取 {selectedLSI.length} 個語意段落</span>
                  </div>
                  <p className="text-xs text-slate-500 mb-6 flex items-center gap-1">
                    <Info className="w-3 h-3" /> 選取的 LSI 將決定大綱生成的章節數量。點擊可加選以擴大 GSC 覆蓋範圍。
                  </p>
                  
                  <div className="flex flex-wrap gap-3">
                    {intentData.lsiKeywords.map(item => (
                      <button 
                        key={item.word}
                        onClick={() => toggleLSI(item.word)}
                        className={`px-4 py-2 rounded-xl border-2 transition-all flex items-center gap-2 ${
                          selectedLSI.includes(item.word) 
                            ? 'bg-blue-600 border-blue-600 text-white shadow-md' 
                            : 'bg-white border-slate-100 text-slate-600 hover:border-blue-200'
                        }`}
                      >
                        <span className="text-sm font-bold">{item.word}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                          selectedLSI.includes(item.word) ? 'bg-blue-500 text-blue-100' : 'bg-slate-100 text-slate-400'
                        }`}>
                          {(item.weight * 100).toFixed(0)}%
                        </span>
                      </button>
                    ))}
                  </div>
                </section>

                <section className="space-y-4">
                  <h3 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                    <MousePointer2 className="text-blue-600 w-6 h-6" /> 挑選最佳標題 (H1)
                  </h3>
                  <div className="grid gap-3">
                    {intentData.suggestedTitles.map((title, idx) => (
                      <div 
                        key={idx}
                        onClick={() => setTempSelectedTitle(title)}
                        className={`p-6 border-2 rounded-2xl cursor-pointer transition-all flex items-center justify-between ${
                          tempSelectedTitle === title 
                            ? 'bg-blue-50 border-blue-600 shadow-lg' 
                            : 'bg-white border-slate-200 hover:border-slate-300 shadow-sm'
                        }`}
                      >
                        <span className={`text-lg font-bold ${tempSelectedTitle === title ? 'text-blue-900' : 'text-slate-700'}`}>{title}</span>
                        {tempSelectedTitle === title && <CheckCircle className="text-blue-600 w-6 h-6 animate-in zoom-in" />}
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            </div>

            <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4 shadow-[0_-10px_40px_rgba(0,0,0,0.05)] z-20">
              <div className="max-w-6xl mx-auto flex items-center justify-between">
                <div className="flex items-center gap-8">
                  <div className="flex flex-col">
                    <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">選取標題</span>
                    <span className={`text-sm font-bold ${tempSelectedTitle ? 'text-blue-600' : 'text-red-400 italic'}`}>
                      {tempSelectedTitle || '尚未選取標題'}
                    </span>
                  </div>
                  <div className="h-8 w-px bg-slate-200" />
                  <div className="flex flex-col">
                    <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">意圖與風格</span>
                    <span className="text-sm font-bold text-slate-700">{intentOptions.find(o => o.value === currentIntent)?.label} | {currentStyle}</span>
                  </div>
                </div>
                
                <button 
                  onClick={handleConfirmStrategy}
                  disabled={!tempSelectedTitle || loading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white px-10 py-4 rounded-xl font-black shadow-xl shadow-blue-200 flex items-center gap-2 transition-all active:scale-95"
                >
                  {loading ? <Loader2 className="animate-spin" /> : <><Layout className="w-5 h-5" /> 產出動態大綱 <ArrowRight className="w-5 h-5" /></>}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 步驟 3: 動態大綱編輯器 */}
        {step === 3 && (
          <div className="max-w-4xl mx-auto space-y-6 animate-in slide-in-from-bottom-8 duration-700">
            <div className="bg-gradient-to-br from-slate-900 to-blue-900 text-white p-10 rounded-3xl shadow-2xl relative overflow-hidden">
              <div className="relative z-10 space-y-4">
                <div className="flex items-center gap-4">
                  <button onClick={() => setStep(2)} className="flex items-center gap-1 text-blue-300 hover:text-white transition-all text-xs font-bold uppercase tracking-widest bg-white/10 px-3 py-1.5 rounded-lg">
                    <Undo2 className="w-3 h-3" /> 返回修改策略
                  </button>
                  <span className="text-white/40 text-xs">|</span>
                  <p className="text-blue-300 text-xs font-bold uppercase tracking-widest">Blueprint Preview</p>
                </div>
                <h2 className="text-3xl font-black leading-tight">{selectedTitle}</h2>
                <div className="flex flex-wrap gap-3">
                  <span className="bg-blue-500/20 border border-blue-400/30 px-3 py-1 rounded-full text-[10px] font-bold">意圖：{currentIntent}</span>
                  <span className="bg-blue-500/20 border border-blue-400/30 px-3 py-1 rounded-full text-[10px] font-bold">風格：{currentStyle}</span>
                  <span className="bg-green-500/20 border border-green-400/30 px-3 py-1 rounded-full text-[10px] font-bold">動態部署 {selectedLSI.length} 個語意章節</span>
                </div>
              </div>
              <Sparkles className="absolute right-[-20px] bottom-[-20px] w-48 h-48 opacity-10" />
            </div>
            
            <div className="bg-white p-8 rounded-3xl border shadow-sm space-y-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xl font-bold flex items-center gap-2 text-slate-800"><Layout className="w-6 h-6 text-blue-600" /> AI 規劃的文章結構</h3>
                <button className="flex items-center gap-1 text-blue-600 text-xs font-bold hover:underline"><Plus className="w-4 h-4" /> 新增章節</button>
              </div>
              
              <div className="space-y-4">
                {outline.map((item) => (
                  <div key={item.id} className="border border-slate-100 rounded-2xl p-6 bg-slate-50 transition-all hover:bg-white hover:border-blue-100 hover:shadow-md">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-4">
                        <GripVertical className="text-slate-200" />
                        <div className="bg-blue-600 text-white px-2 py-0.5 rounded text-[10px] font-bold uppercase">H2 Section</div>
                        <span className="font-bold text-slate-800 text-lg">{item.text}</span>
                      </div>
                      {item.lsi && item.lsi.length > 0 && (
                        <div className="flex gap-2">
                          {item.lsi.map(l => (
                            <span key={l} className="bg-indigo-50 text-indigo-600 text-[10px] px-2 py-1 rounded border border-indigo-100 font-bold">整合語意詞：{l}</span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="ml-14 grid grid-cols-2 gap-3">
                      {item.sub.map((s, idx) => (
                        <div key={idx} className="bg-white border border-slate-100 p-2.5 rounded-xl text-sm text-slate-500 flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                          {s}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-10 flex justify-end items-center gap-6 pt-6 border-t">
                <div className="text-right">
                  <p className="text-xs font-bold text-slate-700">預計產出</p>
                  <p className="text-[10px] text-slate-400">風格：{currentStyle} | 字數約 {outline.length * 450} 字</p>
                </div>
                <button onClick={handleStartWriting} className="bg-blue-600 hover:bg-blue-700 text-white px-10 py-5 rounded-2xl font-black shadow-xl flex items-center gap-2 transition-all active:scale-95">
                  啟動 AI 自動撰寫全文 <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 步驟 4: 撰寫預覽 */}
        {step === 4 && (
          <div className="grid grid-cols-2 gap-8 h-[70vh] animate-in zoom-in-95">
            <div className="bg-white border-2 rounded-3xl p-8 flex flex-col space-y-6 shadow-sm">
              <div className="flex justify-between items-center">
                <h3 className="font-black text-xl text-slate-800">撰寫中...</h3>
                <span className="text-3xl font-black text-blue-600">{writingProgress}%</span>
              </div>
              <div className="w-full bg-slate-100 h-4 rounded-full overflow-hidden shadow-inner">
                <div className="bg-blue-600 h-full transition-all duration-1000" style={{ width: `${writingProgress}%` }} />
              </div>
              <div className="space-y-4 pt-4">
                <div className="flex items-center gap-3 text-green-600 font-bold text-sm bg-green-50 p-3 rounded-xl border border-green-100">
                  <CheckCircle className="w-5 h-5" /> 語意關係注入完成
                </div>
                <div className="flex items-center gap-3 text-slate-600 font-bold text-sm bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <Loader2 className="w-5 h-5 animate-spin" /> 章節分段深度撰寫中 (Style: {currentStyle})
                </div>
              </div>
            </div>
            <div className="bg-white border-2 rounded-3xl p-10 overflow-y-auto font-serif text-slate-800 leading-relaxed text-lg shadow-inner">
              {articleContent || "正在等待 AI 產出第一章節內容..."}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;