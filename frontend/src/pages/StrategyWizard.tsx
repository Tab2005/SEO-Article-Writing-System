import { useState, useEffect } from 'react'
import {
    Search, Settings, CheckCircle, Layout, ArrowRight, ArrowLeft,
    GripVertical, Loader2, TrendingUp, Target, RefreshCw, Info,
    Layers, Sparkles, Lightbulb, Plus, X, Copy, Download, Check
} from 'lucide-react'
import { researchService, AnalysisReport, ResearchJob } from '../services/research.service'
import { contentService } from '../services/content.service'
import { strategyService } from '../services/strategy.service'
import { streamingService, StreamProgressEvent, StreamContentEvent, StreamDoneEvent } from '../services/draft.service'

// Intent options
const intentOptions = [
    { value: 'informational', label: '📚 資訊型', desc: '教學、指南或百科。適合解決疑惑、分享知識。' },
    { value: 'commercial', label: '💰 商業型', desc: '產品評測或對比。適合購物建議、決策參考。' },
    { value: 'transactional', label: '🛒 交易型', desc: '促成購買或服務預約。目標是直接轉單。' },
    { value: 'navigational', label: '🗺️ 導航型', desc: '指引路徑或登入入口。適合品牌官網或地點導引。' }
]

// Style/Tone options
const styleOptions = [
    '專業教育風', '新手友善型', '權威評論風', '強烈號召風', '親切對話風', '簡潔指令風'
]

// LSI Keyword interface for wizard
interface LsiKeyword {
    term: string
    weight: number
    essential: boolean
    source: string
}

// Editable section for outline
interface EditableSection {
    id: string
    heading: string
    level: number
    key_points: string[]
    lsi: string[]
}

function StrategyWizard() {
    // Wizard step state
    const [step, setStep] = useState(1)
    const [loading, setLoading] = useState(false)

    // Step 1: Research
    const [keyword, setKeyword] = useState('')
    const [market, setMarket] = useState('tw')
    const [jobId, setJobId] = useState<string | null>(null)
    const [job, setJob] = useState<ResearchJob | null>(null)
    const [report, setReport] = useState<AnalysisReport | null>(null)

    // Step 2: Strategy
    const [currentIntent, setCurrentIntent] = useState('informational')
    const [currentStyle, setCurrentStyle] = useState('專業教育風')
    const [lsiKeywords, setLsiKeywords] = useState<LsiKeyword[]>([])
    const [selectedLsi, setSelectedLsi] = useState<string[]>([])
    const [suggestedTitles, setSuggestedTitles] = useState<string[]>([])
    const [selectedTitle, setSelectedTitle] = useState('')
    const [tempSelectedTitle, setTempSelectedTitle] = useState('')

    // Step 3: Outline
    const [outline, setOutline] = useState<EditableSection[]>([])
    const [dragIndex, setDragIndex] = useState<number | null>(null)
    const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)

    // Step 4: Content
    const [articleContent, setArticleContent] = useState('')
    const [writingProgress, setWritingProgress] = useState(0)
    const [copied, setCopied] = useState(false)

    // E-E-A-T tips from API
    const [eeatTips, setEeatTips] = useState<string[]>([])

    // ============ Step 1: Research Handlers ============

    const handleStartResearch = async () => {
        if (!keyword.trim()) return
        setLoading(true)

        try {
            const newJob = await researchService.createJob(keyword.trim(), market, 10)
            setJobId(newJob.job_id)
            setJob(newJob)
        } catch (error) {
            console.error('Failed to create research job:', error)
            setLoading(false)
        }
    }

    // Poll for job status
    useEffect(() => {
        if (!jobId || !job) return
        if (job.status === 'completed' || job.status === 'failed') return

        const pollInterval = setInterval(async () => {
            try {
                const updatedJob = await researchService.getJob(jobId)
                setJob(updatedJob)

                if (updatedJob.status === 'completed') {
                    clearInterval(pollInterval)
                    // Fetch report
                    const jobReport = await researchService.getJobReport(jobId)
                    setReport(jobReport)
                    processReportForStrategy(jobReport)
                    setLoading(false)
                    setStep(2)
                } else if (updatedJob.status === 'failed') {
                    clearInterval(pollInterval)
                    setLoading(false)
                }
            } catch (error) {
                console.error('Poll error:', error)
            }
        }, 2000)

        return () => clearInterval(pollInterval)
    }, [jobId, job])

    // Process report data for Step 2 - now uses Strategy API
    const processReportForStrategy = async (jobReport: AnalysisReport) => {
        try {
            // Call Strategy API to get complete strategy pack
            const pack = await strategyService.getStrategyPack({
                keyword: keyword,
                market: market,
                job_id: jobId || undefined,
            })

            // Set LSI keywords from API
            const lsiList: LsiKeyword[] = pack.lsi_keywords.map(kw => ({
                term: kw.term,
                weight: kw.weight,
                essential: kw.essential,
                source: kw.source
            }))
            setLsiKeywords(lsiList)
            setSelectedLsi(lsiList.filter(l => l.essential).map(l => l.term))

            // Set titles from API
            setSuggestedTitles(pack.suggested_titles)

            // Set detected intent
            setCurrentIntent(pack.ai_detected_intent)

            // Set E-E-A-T tips
            setEeatTips(pack.eeat_tips)

        } catch (error) {
            console.error('Failed to get strategy pack:', error)
            // Fallback to local processing
            const lsiList: LsiKeyword[] = []

            if (jobReport.tfidf_analysis) {
                jobReport.tfidf_analysis.suggested_keywords?.slice(0, 5).forEach((kw, idx) => {
                    lsiList.push({
                        term: kw.term,
                        weight: kw.score,
                        essential: idx < 3,
                        source: 'suggested'
                    })
                })
            }

            setLsiKeywords(lsiList)
            setSelectedLsi(lsiList.filter(l => l.essential).map(l => l.term))
            generateTitlesLocal(keyword, 'informational', '專業教育風')
        }
    }

    // ============ Step 2: Strategy Handlers ============

    // Local title generation fallback
    const generateTitlesLocal = (kw: string, intent: string, style: string) => {
        let titles: string[] = []

        if (intent === 'commercial') {
            titles = [
                `2026 評測：${kw}相關產品對比指南`,
                `選購建議：${kw}該怎麼挑？優缺點全解析`,
                `${kw}推薦清單：適合新手的 CP 值之選`
            ]
        } else if (intent === 'transactional') {
            titles = [
                `立即體驗${kw}！限時優惠方案`,
                `${kw}服務預約：專業團隊為您服務`,
                `現在就開始${kw}，享受專屬折扣`
            ]
        } else if (intent === 'navigational') {
            titles = [
                `${kw}官方入口：快速登入與導覽`,
                `前往${kw}：完整路線指南`,
                `${kw}導航：找到您需要的資源`
            ]
        } else {
            const styleLabel = style === '新手友善型' ? '初學者' : '專業人士'
            titles = [
                `想學${kw}必看！2026 最新科學指南`,
                `5 個關於${kw}的核心觀念，讓你事半功倍`,
                `破解${kw}常見迷思：這才是最適合${styleLabel}的策略`
            ]
        }

        setSuggestedTitles(titles)
    }

    // Regenerate titles using API
    const handleRegenerateTitles = async () => {
        setLoading(true)
        try {
            const pack = await strategyService.regenerateTitles(
                keyword,
                currentIntent,
                currentStyle,
                jobId || undefined
            )
            setSuggestedTitles(pack.suggested_titles)
            setEeatTips(pack.eeat_tips)
            setTempSelectedTitle('')
        } catch (error) {
            console.error('Failed to regenerate titles:', error)
            // Fallback to local generation
            generateTitlesLocal(keyword, currentIntent, currentStyle)
            setTempSelectedTitle('')
        } finally {
            setLoading(false)
        }
    }

    const toggleLsi = (term: string) => {
        setSelectedLsi(prev =>
            prev.includes(term) ? prev.filter(t => t !== term) : [...prev, term]
        )
    }

    // ============ Step 3: Outline Handlers ============

    const handleConfirmStrategy = async () => {
        if (!tempSelectedTitle) return
        setSelectedTitle(tempSelectedTitle)
        setLoading(true)

        try {
            // Generate outline via API
            const outlineResult = await contentService.generateOutline({
                topic: tempSelectedTitle,
                target_keyword: keyword,
                secondary_keywords: selectedLsi,
                tone: currentStyle,
                market: market
            })

            // Convert to editable format
            const editableSections: EditableSection[] = outlineResult.sections.map((section, idx) => ({
                id: `section-${idx}`,
                heading: section.heading,
                level: section.level,
                key_points: section.key_points,
                lsi: selectedLsi.filter((_, i) => i === idx % selectedLsi.length ? true : false)
            }))

            setOutline(editableSections)
            setLoading(false)
            setStep(3)
        } catch (error) {
            console.error('Failed to generate outline:', error)
            // Fallback: generate outline locally
            const fallbackSections: EditableSection[] = [
                { id: 'intro', heading: `導言：為什麼「${keyword}」是您今年必須掌握的關鍵？`, level: 2, key_points: ['趨勢背景', '核心價值與目標'], lsi: [] }
            ]

            selectedLsi.forEach((lsi, index) => {
                fallbackSections.push({
                    id: `h2-${index}`,
                    heading: `深度解析：${lsi} 如何決定您的${keyword}成效`,
                    level: 2,
                    key_points: [`${lsi} 的運作機制`, '針對新手的實踐技巧', '常見優化建議'],
                    lsi: [lsi]
                })
            })

            fallbackSections.push({
                id: 'conclusion',
                heading: '結語與常見問題：邁向成功的最後建議',
                level: 2,
                key_points: ['FAQ 疑難排解', '後續行動清單'],
                lsi: []
            })

            setOutline(fallbackSections)
            setLoading(false)
            setStep(3)
        }
    }

    const updateSectionHeading = (index: number, heading: string) => {
        setOutline(prev => prev.map((s, i) => i === index ? { ...s, heading } : s))
    }

    const removeSection = (index: number) => {
        setOutline(prev => prev.filter((_, i) => i !== index))
    }

    const addSection = () => {
        const newSection: EditableSection = {
            id: `section-${Date.now()}`,
            heading: '新章節',
            level: 2,
            key_points: ['重點 1', '重點 2'],
            lsi: []
        }
        setOutline(prev => [...prev, newSection])
    }

    // Drag and drop
    const handleDragStart = (index: number) => {
        setDragIndex(index)
    }

    const handleDragOver = (e: React.DragEvent, index: number) => {
        e.preventDefault()
        setDragOverIndex(index)
    }

    const handleDragEnd = () => {
        if (dragIndex !== null && dragOverIndex !== null && dragIndex !== dragOverIndex) {
            const newOutline = [...outline]
            const [removed] = newOutline.splice(dragIndex, 1)
            newOutline.splice(dragOverIndex, 0, removed)
            setOutline(newOutline)
        }
        setDragIndex(null)
        setDragOverIndex(null)
    }

    // ============ Step 4: Content Generation with SSE ============

    const [currentSection, setCurrentSection] = useState('')
    const [isStreaming, setIsStreaming] = useState(false)

    const handleStartWriting = async () => {
        setStep(4)
        setWritingProgress(0)
        setArticleContent('')
        setCurrentSection('')
        setIsStreaming(true)

        // Build outline data for streaming API
        const outlineData = {
            sections: outline.map(section => ({
                heading: section.heading,
                level: section.level,
                key_points: section.key_points,
            })),
            meta_description: `${keyword} 完整指南`,
            estimated_word_count: outline.length * 450,
        }

        const streamRequest = {
            title: selectedTitle,
            target_keyword: keyword,
            outline: outlineData,
            secondary_keywords: selectedLsi,
            tone: currentStyle,
        }

        const { startStreaming } = streamingService.createEventSource(streamRequest)

        try {
            await startStreaming(
                // onProgress
                (event: StreamProgressEvent) => {
                    setCurrentSection(event.section)
                    setWritingProgress(event.progress)
                },
                // onContent
                (event: StreamContentEvent) => {
                    setArticleContent(prev => prev + event.content)
                },
                // onDone
                (event: StreamDoneEvent) => {
                    setWritingProgress(100)
                    setArticleContent(event.content)
                    setIsStreaming(false)
                    setCurrentSection('')
                },
                // onError
                (error: Error) => {
                    console.error('Streaming error:', error)
                    setIsStreaming(false)
                    // Fallback to non-streaming generation
                    handleFallbackGeneration()
                }
            )
        } catch (error) {
            console.error('Failed to start streaming:', error)
            handleFallbackGeneration()
        }
    }

    // Fallback to regular content generation if streaming fails
    const handleFallbackGeneration = async () => {
        setWritingProgress(10)

        // Simulate progress
        let progress = 10
        const interval = setInterval(() => {
            progress += 5
            setWritingProgress(Math.min(progress, 90))
            if (progress >= 90) clearInterval(interval)
        }, 500)

        try {
            const result = await contentService.generateContent({
                topic: selectedTitle,
                target_keyword: keyword,
                secondary_keywords: selectedLsi,
                word_count_target: outline.length * 450,
                tone: currentStyle,
                market: market
            })

            clearInterval(interval)
            setWritingProgress(100)
            setArticleContent(result.content)
        } catch (error) {
            console.error('Fallback generation failed:', error)
            clearInterval(interval)
            setWritingProgress(100)
            setArticleContent(`# ${selectedTitle}\n\n生成失敗，請重試。`)
        }
    }

    const copyToClipboard = async () => {
        try {
            await navigator.clipboard.writeText(articleContent)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        } catch (error) {
            console.error('Copy failed:', error)
        }
    }

    const downloadMarkdown = () => {
        const blob = new Blob([articleContent], { type: 'text/markdown' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${keyword.replace(/\s+/g, '_')}_article.md`
        a.click()
        URL.revokeObjectURL(url)
    }

    // ============ Render ============

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-900 pb-24">
            {/* Header with Stepper */}
            <div className="bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700 px-8 py-4 sticky top-0 z-20">
                <div className="max-w-6xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
                            <TrendingUp className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900 dark:text-white">策略導引 Wizard</h1>
                            <p className="text-sm text-gray-500 dark:text-gray-400">4 步驟完成 SEO 內容策略</p>
                        </div>
                    </div>

                    {/* Stepper */}
                    <div className="flex items-center gap-4">
                        {[1, 2, 3, 4].map(s => (
                            <div key={s} className="flex items-center">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${step >= s
                                    ? 'bg-primary-600 text-white shadow-lg shadow-primary-200 dark:shadow-primary-900/30'
                                    : 'bg-gray-200 dark:bg-slate-700 text-gray-500 dark:text-gray-400'
                                    }`}>
                                    {step > s ? <CheckCircle className="w-5 h-5" /> : s}
                                </div>
                                {s < 4 && (
                                    <div className={`w-12 h-1 mx-2 rounded-full transition-all ${step > s ? 'bg-primary-600' : 'bg-gray-200 dark:bg-slate-700'
                                        }`} />
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <main className="max-w-6xl mx-auto p-8">
                {/* Step 1: Research */}
                {step === 1 && (
                    <div className="max-w-2xl mx-auto space-y-8 py-12 animate-in fade-in duration-500">
                        <div className="text-center space-y-4">
                            <h2 className="text-4xl font-black text-gray-800 dark:text-white tracking-tight">內容策略研究控制台</h2>
                            <p className="text-gray-500 dark:text-gray-400 text-lg">輸入您的目標關鍵字，AI 將掃描前 10 名競品並擬定排位計畫。</p>
                        </div>

                        <div className="bg-white dark:bg-slate-800 p-10 rounded-3xl shadow-2xl border border-gray-100 dark:border-slate-700">
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">主要關鍵字</label>
                                    <div className="relative">
                                        <Search className="absolute left-4 top-4 text-gray-400 w-5 h-5" />
                                        <input
                                            type="text"
                                            className="w-full pl-12 pr-4 py-4 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-2xl focus:ring-2 focus:ring-primary-500 outline-none text-lg text-gray-900 dark:text-white placeholder-gray-400"
                                            placeholder="例如：想學減脂..."
                                            value={keyword}
                                            onChange={(e) => setKeyword(e.target.value)}
                                            onKeyDown={(e) => e.key === 'Enter' && handleStartResearch()}
                                        />
                                    </div>
                                </div>

                                {/* Job Status */}
                                {job && (
                                    <div className={`p-4 rounded-xl ${job.status === 'completed' ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800' :
                                        job.status === 'failed' ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800' :
                                            'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                                        }`}>
                                        <div className="flex items-center gap-3">
                                            {job.status === 'completed' ? (
                                                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                                            ) : job.status === 'failed' ? (
                                                <X className="w-5 h-5 text-red-600 dark:text-red-400" />
                                            ) : (
                                                <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin" />
                                            )}
                                            <div className="flex-1">
                                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                                    {job.message || `狀態：${job.status}`}
                                                </p>
                                                {job.progress > 0 && job.progress < 100 && (
                                                    <div className="mt-2 w-full bg-gray-200 dark:bg-slate-600 rounded-full h-2">
                                                        <div
                                                            className="bg-primary-600 h-2 rounded-full transition-all"
                                                            style={{ width: `${job.progress}%` }}
                                                        />
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                <button
                                    onClick={handleStartResearch}
                                    disabled={loading || !keyword.trim()}
                                    className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 dark:disabled:bg-slate-600 text-white font-bold py-5 rounded-2xl shadow-xl flex items-center justify-center gap-2 transition-all"
                                >
                                    {loading ? <Loader2 className="animate-spin" /> : <><Target className="w-5 h-5" /> 開始競品分析</>}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 2: Strategy */}
                {step === 2 && report && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
                        {/* AI Status Banner */}
                        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 p-4 rounded-xl flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Sparkles className="text-primary-600 dark:text-primary-400 w-5 h-5" />
                                <p className="text-sm text-blue-800 dark:text-blue-200 font-medium">
                                    策略建議已產出！分析了 {report.competitor_count} 個競品，平均字數 {report.avg_word_count} 字。
                                </p>
                            </div>
                            <div className="flex items-center gap-2 px-3 py-1 bg-white dark:bg-slate-800 rounded-lg border border-blue-200 dark:border-blue-700">
                                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                <span className="text-xs font-bold text-primary-600 dark:text-primary-400 uppercase">AI Ready</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-12 gap-8">
                            {/* Left Panel: Settings */}
                            <div className="col-span-4 space-y-6">
                                <section className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-sm space-y-6">
                                    <h3 className="font-bold flex items-center gap-2 text-gray-800 dark:text-white border-b border-gray-100 dark:border-slate-700 pb-4">
                                        <Settings className="w-5 h-5 text-primary-600" /> 文章策略核心
                                    </h3>

                                    {/* Intent Picker */}
                                    <div className="space-y-3">
                                        <label className="text-xs font-bold text-gray-400 uppercase tracking-widest">搜尋意圖 (Intent)</label>
                                        <div className="grid gap-2">
                                            {intentOptions.map(opt => (
                                                <button
                                                    key={opt.value}
                                                    onClick={() => setCurrentIntent(opt.value)}
                                                    className={`text-left p-3 rounded-xl border-2 transition-all relative ${currentIntent === opt.value
                                                        ? 'bg-primary-50 dark:bg-primary-900/20 border-primary-600 shadow-sm'
                                                        : 'bg-gray-50 dark:bg-slate-700 border-transparent hover:border-gray-200 dark:hover:border-slate-600'
                                                        }`}
                                                >
                                                    <p className={`text-sm font-bold ${currentIntent === opt.value ? 'text-primary-700 dark:text-primary-400' : 'text-gray-700 dark:text-gray-300'}`}>
                                                        {opt.label}
                                                    </p>
                                                    <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1 leading-tight">{opt.desc}</p>
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Tone Picker */}
                                    <div className="space-y-3">
                                        <label className="text-xs font-bold text-gray-400 uppercase tracking-widest">建議風格 (Tone)</label>
                                        <select
                                            className="w-full p-3 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-xl text-sm font-bold text-gray-700 dark:text-gray-300 outline-none focus:ring-2 focus:ring-primary-500"
                                            value={currentStyle}
                                            onChange={(e) => setCurrentStyle(e.target.value)}
                                        >
                                            {styleOptions.map(s => <option key={s} value={s}>{s}</option>)}
                                        </select>
                                    </div>

                                    {/* Regenerate Button */}
                                    <button
                                        onClick={handleRegenerateTitles}
                                        disabled={loading}
                                        className="w-full py-4 bg-gray-900 dark:bg-slate-600 text-white rounded-xl text-sm font-bold flex items-center justify-center gap-2 hover:bg-black dark:hover:bg-slate-500 transition-all shadow-md active:scale-95"
                                    >
                                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><RefreshCw className="w-4 h-4" /> 應用策略並重產標題</>}
                                    </button>
                                </section>

                                {/* E-E-A-T Tips */}
                                <section className="bg-gray-900 dark:bg-slate-950 p-6 rounded-2xl text-white shadow-lg">
                                    <h3 className="text-sm font-bold flex items-center gap-2 mb-4 text-primary-400">
                                        <Lightbulb className="w-4 h-4" /> 專家撰寫建議 (E-E-A-T)
                                    </h3>
                                    <div className="space-y-4">
                                        <p className="text-xs text-gray-300 leading-relaxed">
                                            對於關鍵字「{keyword}」，前 {report.competitor_count} 名競品平均字數為 {report.avg_word_count} 字。建議：
                                        </p>
                                        <ul className="text-[10px] text-gray-400 space-y-2 list-disc pl-4">
                                            {eeatTips.length > 0 ? (
                                                eeatTips.map((tip, idx) => (
                                                    <li key={idx}>{tip}</li>
                                                ))
                                            ) : (
                                                <>
                                                    <li>強化「經驗 (Experience)」：加入實際測試或個人心得。</li>
                                                    <li>對齊「{currentIntent === 'informational' ? '教學' : '評測'}」邏輯。</li>
                                                    <li>使用「{currentStyle}」可以讓跳出率降低 15%。</li>
                                                </>
                                            )}
                                        </ul>
                                    </div>
                                </section>
                            </div>

                            {/* Right Panel: LSI & Titles */}
                            <div className="col-span-8 space-y-8">
                                {/* LSI Keywords */}
                                <section className="bg-white dark:bg-slate-800 p-8 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-sm">
                                    <div className="flex items-center justify-between mb-2">
                                        <h4 className="font-bold text-gray-800 dark:text-white flex items-center gap-2 text-lg">
                                            <Layers className="w-5 h-5 text-primary-600" /> 語意關鍵字補強 (LSI)
                                        </h4>
                                        <span className="text-xs text-gray-400 font-medium">已選取 {selectedLsi.length} 個語意段落</span>
                                    </div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-6 flex items-center gap-1">
                                        <Info className="w-3 h-3" /> 選取的 LSI 將決定大綱生成的章節數量。
                                    </p>

                                    <div className="flex flex-wrap gap-3">
                                        {lsiKeywords.map(item => (
                                            <button
                                                key={item.term}
                                                onClick={() => toggleLsi(item.term)}
                                                className={`px-4 py-2 rounded-xl border-2 transition-all flex items-center gap-2 ${selectedLsi.includes(item.term)
                                                    ? 'bg-primary-600 border-primary-600 text-white shadow-md'
                                                    : 'bg-white dark:bg-slate-700 border-gray-100 dark:border-slate-600 text-gray-600 dark:text-gray-300 hover:border-primary-200 dark:hover:border-primary-700'
                                                    }`}
                                            >
                                                <span className="text-sm font-bold">{item.term}</span>
                                                <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${selectedLsi.includes(item.term) ? 'bg-primary-500 text-primary-100' : 'bg-gray-100 dark:bg-slate-600 text-gray-400 dark:text-gray-500'
                                                    }`}>
                                                    {(item.weight * 100).toFixed(0)}%
                                                </span>
                                            </button>
                                        ))}
                                    </div>
                                </section>

                                {/* Title Picker */}
                                <section className="space-y-4">
                                    <h3 className="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
                                        <Target className="text-primary-600 w-6 h-6" /> 挑選最佳標題 (H1)
                                    </h3>
                                    <div className="grid gap-3">
                                        {suggestedTitles.map((title, idx) => (
                                            <div
                                                key={idx}
                                                onClick={() => setTempSelectedTitle(title)}
                                                className={`p-6 border-2 rounded-2xl cursor-pointer transition-all flex items-center justify-between ${tempSelectedTitle === title
                                                    ? 'bg-primary-50 dark:bg-primary-900/20 border-primary-600 shadow-lg'
                                                    : 'bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600 shadow-sm'
                                                    }`}
                                            >
                                                <span className={`text-lg font-bold ${tempSelectedTitle === title ? 'text-primary-900 dark:text-primary-300' : 'text-gray-700 dark:text-gray-300'}`}>
                                                    {title}
                                                </span>
                                                {tempSelectedTitle === title && <CheckCircle className="text-primary-600 w-6 h-6" />}
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            </div>
                        </div>

                        {/* Bottom CTA Bar */}
                        <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700 p-4 shadow-lg z-20">
                            <div className="max-w-6xl mx-auto flex items-center justify-between">
                                <div className="flex items-center gap-8">
                                    <div className="flex flex-col">
                                        <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">選取標題</span>
                                        <span className={`text-sm font-bold ${tempSelectedTitle ? 'text-primary-600 dark:text-primary-400' : 'text-red-400 italic'}`}>
                                            {tempSelectedTitle || '尚未選取標題'}
                                        </span>
                                    </div>
                                    <div className="h-8 w-px bg-gray-200 dark:bg-slate-700" />
                                    <div className="flex flex-col">
                                        <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">意圖與風格</span>
                                        <span className="text-sm font-bold text-gray-700 dark:text-gray-300">
                                            {intentOptions.find(o => o.value === currentIntent)?.label} | {currentStyle}
                                        </span>
                                    </div>
                                </div>

                                <button
                                    onClick={handleConfirmStrategy}
                                    disabled={!tempSelectedTitle || loading}
                                    className="bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 dark:disabled:bg-slate-600 text-white px-10 py-4 rounded-xl font-black shadow-xl flex items-center gap-2 transition-all active:scale-95"
                                >
                                    {loading ? <Loader2 className="animate-spin" /> : <><Layout className="w-5 h-5" /> 產出動態大綱 <ArrowRight className="w-5 h-5" /></>}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 3: Outline Editor */}
                {step === 3 && (
                    <div className="max-w-4xl mx-auto space-y-6 animate-in slide-in-from-right-4 duration-500">
                        {/* Header Card */}
                        <div className="bg-gradient-to-br from-gray-900 to-primary-900 text-white p-10 rounded-3xl shadow-2xl relative overflow-hidden">
                            <div className="relative z-10 space-y-4">
                                <div className="flex items-center gap-4">
                                    <button
                                        onClick={() => setStep(2)}
                                        className="flex items-center gap-1 text-primary-300 hover:text-white transition-all text-xs font-bold uppercase tracking-widest bg-white/10 px-3 py-1.5 rounded-lg"
                                    >
                                        <ArrowLeft className="w-3 h-3" /> 返回修改策略
                                    </button>
                                    <span className="text-white/40 text-xs">|</span>
                                    <p className="text-primary-300 text-xs font-bold uppercase tracking-widest">Blueprint Preview</p>
                                </div>
                                <h2 className="text-3xl font-black leading-tight">{selectedTitle}</h2>
                                <div className="flex flex-wrap gap-3">
                                    <span className="bg-primary-500/20 border border-primary-400/30 px-3 py-1 rounded-full text-[10px] font-bold">
                                        意圖：{intentOptions.find(o => o.value === currentIntent)?.label}
                                    </span>
                                    <span className="bg-primary-500/20 border border-primary-400/30 px-3 py-1 rounded-full text-[10px] font-bold">
                                        風格：{currentStyle}
                                    </span>
                                    <span className="bg-green-500/20 border border-green-400/30 px-3 py-1 rounded-full text-[10px] font-bold">
                                        動態部署 {selectedLsi.length} 個語意章節
                                    </span>
                                </div>
                            </div>
                            <Sparkles className="absolute right-[-20px] bottom-[-20px] w-48 h-48 opacity-10" />
                        </div>

                        {/* Outline Editor */}
                        <div className="bg-white dark:bg-slate-800 p-8 rounded-3xl border border-gray-200 dark:border-slate-700 shadow-sm space-y-6">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="text-xl font-bold flex items-center gap-2 text-gray-800 dark:text-white">
                                    <Layout className="w-6 h-6 text-primary-600" /> AI 規劃的文章結構
                                </h3>
                                <button
                                    onClick={addSection}
                                    className="flex items-center gap-1 text-primary-600 text-xs font-bold hover:underline"
                                >
                                    <Plus className="w-4 h-4" /> 新增章節
                                </button>
                            </div>

                            <div className="space-y-4">
                                {outline.map((item, index) => (
                                    <div
                                        key={item.id}
                                        draggable
                                        onDragStart={() => handleDragStart(index)}
                                        onDragOver={(e) => handleDragOver(e, index)}
                                        onDragEnd={handleDragEnd}
                                        className={`border rounded-2xl p-6 transition-all ${dragOverIndex === index
                                            ? 'border-primary-400 bg-primary-50 dark:bg-primary-900/20'
                                            : 'border-gray-100 dark:border-slate-700 bg-gray-50 dark:bg-slate-700/50 hover:bg-white dark:hover:bg-slate-700 hover:border-primary-100 dark:hover:border-primary-800 hover:shadow-md'
                                            }`}
                                    >
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex items-center gap-4">
                                                <GripVertical className="text-gray-300 dark:text-gray-600 cursor-grab" />
                                                <div className="bg-primary-600 text-white px-2 py-0.5 rounded text-[10px] font-bold uppercase">H2 Section</div>
                                                <input
                                                    type="text"
                                                    value={item.heading}
                                                    onChange={(e) => updateSectionHeading(index, e.target.value)}
                                                    className="font-bold text-gray-800 dark:text-white text-lg bg-transparent border-none outline-none focus:ring-0 flex-1"
                                                />
                                            </div>
                                            <div className="flex items-center gap-2">
                                                {item.lsi.length > 0 && item.lsi.map(l => (
                                                    <span key={l} className="bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-[10px] px-2 py-1 rounded border border-indigo-100 dark:border-indigo-800 font-bold">
                                                        {l}
                                                    </span>
                                                ))}
                                                <button
                                                    onClick={() => removeSection(index)}
                                                    className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                                                >
                                                    <X className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </div>
                                        <div className="ml-14 grid grid-cols-2 gap-3">
                                            {item.key_points.map((point, idx) => (
                                                <div key={idx} className="bg-white dark:bg-slate-600 border border-gray-100 dark:border-slate-500 p-2.5 rounded-xl text-sm text-gray-500 dark:text-gray-300 flex items-center gap-2">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-primary-400" />
                                                    {point}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Generate Button */}
                            <div className="mt-10 flex justify-end items-center gap-6 pt-6 border-t border-gray-100 dark:border-slate-700">
                                <div className="text-right">
                                    <p className="text-xs font-bold text-gray-700 dark:text-gray-300">預計產出</p>
                                    <p className="text-[10px] text-gray-400">風格：{currentStyle} | 字數約 {outline.length * 450} 字</p>
                                </div>
                                <button
                                    onClick={handleStartWriting}
                                    className="bg-primary-600 hover:bg-primary-700 text-white px-10 py-5 rounded-2xl font-black shadow-xl flex items-center gap-2 transition-all active:scale-95"
                                >
                                    啟動 AI 自動撰寫全文 <ArrowRight className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 4: Writing Preview */}
                {step === 4 && (
                    <div className="grid grid-cols-2 gap-8 h-[70vh] animate-in fade-in duration-500">
                        {/* Left: Progress */}
                        <div className="bg-white dark:bg-slate-800 border-2 border-gray-200 dark:border-slate-700 rounded-3xl p-8 flex flex-col space-y-6 shadow-sm">
                            <div className="flex justify-between items-center">
                                <div>
                                    <h3 className="font-black text-xl text-gray-800 dark:text-white">
                                        {writingProgress < 100 ? '撰寫中...' : '生成完成！'}
                                    </h3>
                                    {isStreaming && currentSection && (
                                        <p className="text-sm text-primary-600 dark:text-primary-400 mt-1">
                                            正在生成：{currentSection}
                                        </p>
                                    )}
                                </div>
                                <span className="text-3xl font-black text-primary-600">{writingProgress}%</span>
                            </div>
                            <div className="w-full bg-gray-100 dark:bg-slate-700 h-4 rounded-full overflow-hidden shadow-inner">
                                <div
                                    className="bg-primary-600 h-full transition-all duration-500"
                                    style={{ width: `${writingProgress}%` }}
                                />
                            </div>

                            <div className="space-y-4 pt-4 flex-1">
                                <div className={`flex items-center gap-3 font-bold text-sm p-3 rounded-xl border ${writingProgress >= 30
                                    ? 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-100 dark:border-green-800'
                                    : 'text-gray-400 bg-gray-50 dark:bg-slate-700 border-gray-100 dark:border-slate-600'
                                    }`}>
                                    {writingProgress >= 30 ? <CheckCircle className="w-5 h-5" /> : <Loader2 className="w-5 h-5 animate-spin" />}
                                    語意關係注入
                                </div>
                                <div className={`flex items-center gap-3 font-bold text-sm p-3 rounded-xl border ${writingProgress >= 60
                                    ? 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-100 dark:border-green-800'
                                    : 'text-gray-400 bg-gray-50 dark:bg-slate-700 border-gray-100 dark:border-slate-600'
                                    }`}>
                                    {writingProgress >= 60 ? <CheckCircle className="w-5 h-5" /> : <Loader2 className="w-5 h-5 animate-spin" />}
                                    章節分段撰寫中 ({currentStyle})
                                </div>
                                <div className={`flex items-center gap-3 font-bold text-sm p-3 rounded-xl border ${writingProgress >= 100
                                    ? 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-100 dark:border-green-800'
                                    : 'text-gray-400 bg-gray-50 dark:bg-slate-700 border-gray-100 dark:border-slate-600'
                                    }`}>
                                    {writingProgress >= 100 ? <CheckCircle className="w-5 h-5" /> : <Loader2 className="w-5 h-5 animate-spin" />}
                                    內容優化與校驗
                                </div>
                            </div>

                            {/* Action Buttons */}
                            {writingProgress >= 100 && (
                                <div className="flex gap-3 pt-4 border-t border-gray-100 dark:border-slate-700">
                                    <button
                                        onClick={copyToClipboard}
                                        className="flex-1 flex items-center justify-center gap-2 py-3 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 rounded-xl font-bold text-gray-700 dark:text-gray-300 transition-colors"
                                    >
                                        {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                                        {copied ? '已複製' : '複製'}
                                    </button>
                                    <button
                                        onClick={downloadMarkdown}
                                        className="flex-1 flex items-center justify-center gap-2 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl font-bold text-white transition-colors"
                                    >
                                        <Download className="w-4 h-4" /> 下載 Markdown
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Right: Preview */}
                        <div className="bg-white dark:bg-slate-800 border-2 border-gray-200 dark:border-slate-700 rounded-3xl p-10 overflow-y-auto shadow-sm">
                            <div className="prose prose-lg dark:prose-invert max-w-none">
                                {articleContent ? (
                                    <div className="whitespace-pre-wrap font-serif text-gray-800 dark:text-gray-200 leading-relaxed">
                                        {articleContent}
                                    </div>
                                ) : (
                                    <p className="text-gray-400 dark:text-gray-500 italic">正在等待 AI 產出內容...</p>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    )
}

export default StrategyWizard
