import { useEffect, useState } from 'react'
import { Search, Loader2, Globe, FileText, BarChart3, ExternalLink, ChevronDown, ChevronUp, AlertCircle, Hash, Heading1, Clock, Sparkles, Tags, TrendingUp, History, Trash2, Eye } from 'lucide-react'
import { researchService, AnalysisReport, CompetitorData, TopicTheme, ResearchJob } from '../services/research.service'

function Research() {
    const [keyword, setKeyword] = useState('')
    const [market, setMarket] = useState('tw')
    const [isLoading, setIsLoading] = useState(false)
    const [results, setResults] = useState<AnalysisReport | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [expandedCompetitor, setExpandedCompetitor] = useState<number | null>(null)

    const [job, setJob] = useState<ResearchJob | null>(null)

    // Topic themes state
    const [isAnalyzingThemes, setIsAnalyzingThemes] = useState(false)
    const [topicThemes, setTopicThemes] = useState<TopicTheme[]>([])

    // Job history state
    const [showHistory, setShowHistory] = useState(false)
    const [jobHistory, setJobHistory] = useState<ResearchJob[]>([])
    const [isLoadingHistory, setIsLoadingHistory] = useState(false)

    // Load job history
    const loadJobHistory = async () => {
        setIsLoadingHistory(true)
        try {
            const jobs = await researchService.listJobs({ limit: 20 })
            setJobHistory(jobs)
        } catch (err) {
            console.error('Failed to load job history:', err)
        } finally {
            setIsLoadingHistory(false)
        }
    }

    // Load history on mount and when showHistory changes
    useEffect(() => {
        if (showHistory) {
            loadJobHistory()
        }
    }, [showHistory])

    // Load a previous job's results
    const loadPreviousJob = async (jobId: string) => {
        setIsLoading(true)
        setError(null)
        setResults(null)
        setTopicThemes([])
        try {
            const jobData = await researchService.getJob(jobId)
            setJob(jobData)
            setKeyword(jobData.keyword)
            setMarket(jobData.market)
            
            if (jobData.status === 'completed' || jobData.status === 'partial') {
                const report = await researchService.getJobReport(jobId)
                setResults(report)
            } else if (jobData.status === 'failed') {
                setError(jobData.error || jobData.message || '此任務執行失敗')
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || '載入失敗')
        } finally {
            setIsLoading(false)
            setShowHistory(false)
        }
    }

    // Delete a job
    const deleteJob = async (jobId: string, e: React.MouseEvent) => {
        e.stopPropagation()
        if (!confirm('確定要刪除此任務嗎？')) return
        try {
            await researchService.deleteJob(jobId)
            setJobHistory(prev => prev.filter(j => j.job_id !== jobId))
        } catch (err) {
            console.error('Failed to delete job:', err)
        }
    }

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!keyword.trim()) return

        setIsLoading(true)
        setError(null)
        setResults(null)
        setJob(null)
        setTopicThemes([])  // Reset themes on new search

        try {
            const created = await researchService.createJob(keyword.trim(), market, 10)
            setJob(created)
            // results will be loaded once the job is completed
            // Refresh history after creating new job
            loadJobHistory()
        } catch (err: any) {
            const message = err.response?.data?.detail || err.message || '分析失敗，請稍後再試'
            setError(message)
            setIsLoading(false)
        } finally {
            // keep loading state until job completes (handled by polling)
        }
    }

    // Poll job status until completed/failed
    useEffect(() => {
        if (!job?.job_id) return

        let cancelled = false
        let timer: any

        const poll = async () => {
            try {
                const latest = await researchService.getJob(job.job_id)
                if (cancelled) return
                setJob(latest)

                if (latest.status === 'completed' || latest.status === 'partial') {
                    const report = await researchService.getJobReport(latest.job_id)
                    if (cancelled) return
                    setResults(report)
                    setIsLoading(false)
                    clearInterval(timer)
                }

                if (latest.status === 'failed') {
                    setIsLoading(false)
                    setError(latest.error || latest.message || '分析失敗，請稍後再試')
                    clearInterval(timer)
                }
            } catch (e: any) {
                if (cancelled) return
                setIsLoading(false)
                setError(e.response?.data?.detail || e.message || '分析失敗，請稍後再試')
                clearInterval(timer)
            }
        }

        // immediate poll then interval
        poll()
        timer = setInterval(poll, 2000)

        return () => {
            cancelled = true
            clearInterval(timer)
        }
    }, [job?.job_id])

    const handleAnalyzeThemes = async () => {
        if (!results) return

        setIsAnalyzingThemes(true)
        try {
            // Collect H2 headings from all competitors
            const headings = results.competitors.map(comp => comp.headings.h2)
            const response = await researchService.analyzeTopicThemes(results.keyword, headings)
            setTopicThemes(response.topic_themes || [])
        } catch (err: any) {
            console.error('Theme analysis failed:', err)
        } finally {
            setIsAnalyzingThemes(false)
        }
    }

    const toggleCompetitor = (rank: number) => {
        setExpandedCompetitor(expandedCompetitor === rank ? null : rank)
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">關鍵字研究</h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        輸入關鍵字以分析競爭對手和 SERP 結果
                    </p>
                </div>
                <button
                    onClick={() => setShowHistory(!showHistory)}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                    <History className="w-4 h-4" />
                    {showHistory ? '隱藏歷史' : '查看歷史'}
                </button>
            </div>

            {/* Job History Panel */}
            {showHistory && (
                <div className="card">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                            <History className="w-5 h-5" />
                            研究任務歷史
                        </h3>
                        <button
                            onClick={loadJobHistory}
                            disabled={isLoadingHistory}
                            className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
                        >
                            {isLoadingHistory ? '載入中...' : '重新整理'}
                        </button>
                    </div>
                    
                    {isLoadingHistory ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                        </div>
                    ) : jobHistory.length === 0 ? (
                        <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                            尚無研究任務記錄
                        </p>
                    ) : (
                        <div className="divide-y divide-gray-200 dark:divide-gray-700">
                            {jobHistory.map((historyJob) => (
                                <div
                                    key={historyJob.job_id}
                                    className="py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800/50 -mx-4 px-4 cursor-pointer transition-colors"
                                    onClick={() => loadPreviousJob(historyJob.job_id)}
                                >
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <span className="font-medium text-gray-900 dark:text-white truncate">
                                                {historyJob.keyword}
                                            </span>
                                            <span className={`px-2 py-0.5 text-xs rounded-full ${
                                                historyJob.status === 'completed' 
                                                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                                    : historyJob.status === 'failed'
                                                    ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                                                    : historyJob.status === 'running'
                                                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                                                    : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-400'
                                            }`}>
                                                {historyJob.status === 'completed' ? '完成' 
                                                    : historyJob.status === 'failed' ? '失敗'
                                                    : historyJob.status === 'running' ? '執行中'
                                                    : historyJob.status === 'partial' ? '部分完成'
                                                    : '等待中'}
                                            </span>
                                        </div>
                                        <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                            <span className="capitalize">{historyJob.market}</span>
                                            {' · '}
                                            {new Date(historyJob.created_at).toLocaleString('zh-TW')}
                                            {historyJob.status === 'completed' && historyJob.completed_at && (
                                                <> · 耗時 {Math.round((new Date(historyJob.completed_at).getTime() - new Date(historyJob.created_at).getTime()) / 1000)}秒</>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 ml-4">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                loadPreviousJob(historyJob.job_id)
                                            }}
                                            className="p-2 text-gray-500 hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-400"
                                            title="查看結果"
                                        >
                                            <Eye className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={(e) => deleteJob(historyJob.job_id, e)}
                                            className="p-2 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
                                            title="刪除任務"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Search Form */}
            <form onSubmit={handleSearch} className="card">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            目標關鍵字
                        </label>
                        <div className="relative">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                            <input
                                type="text"
                                value={keyword}
                                onChange={(e) => setKeyword(e.target.value)}
                                placeholder="例如：義大利麵做法"
                                className="input pl-12"
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <div className="w-full md:w-40">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            目標市場
                        </label>
                        <select
                            value={market}
                            onChange={(e) => setMarket(e.target.value)}
                            className="input"
                            disabled={isLoading}
                        >
                            <option value="tw">台灣</option>
                            <option value="hk">香港</option>
                            <option value="us">美國</option>
                            <option value="jp">日本</option>
                        </select>
                    </div>

                    <div className="flex items-end">
                        <button
                            type="submit"
                            disabled={isLoading || !keyword.trim()}
                            className="btn-primary w-full md:w-auto flex items-center justify-center disabled:opacity-50"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin mr-2" />
                                    分析中...
                                </>
                            ) : (
                                <>
                                    <Search className="w-5 h-5 mr-2" />
                                    開始分析
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </form>

            {/* Error Message */}
            {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <div>
                        <p className="font-medium text-red-800">分析失敗</p>
                        <p className="text-red-700 text-sm mt-1">{error}</p>
                    </div>
                </div>
            )}

            {/* Loading State */}
            {isLoading && (
                <div className="card flex flex-col items-center justify-center py-16">
                    <Loader2 className="w-12 h-12 text-primary-600 animate-spin mb-4" />
                    <p className="text-lg font-medium text-gray-900">正在分析競爭對手...</p>
                    <p className="text-gray-500 text-sm mt-2">
                        {job?.message ? job.message : '這可能需要 30 秒到 1 分鐘'}
                    </p>
                    {typeof job?.progress === 'number' && (
                        <div className="w-full max-w-md mt-6">
                            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    className="h-2 bg-primary-600 rounded-full transition-all"
                                    style={{ width: `${Math.min(100, Math.max(0, job.progress))}%` }}
                                />
                            </div>
                            <p className="text-xs text-gray-500 mt-2 text-center">{job.progress}%</p>
                        </div>
                    )}
                </div>
            )}

            {/* Results */}
            {results && !isLoading && (
                <>
                    {/* Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="card">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                                    <BarChart3 className="w-5 h-5 text-blue-600" />
                                </div>
                                <h3 className="font-semibold text-gray-900">平均字數</h3>
                            </div>
                            <p className="text-3xl font-bold text-gray-900">
                                {results.avg_word_count.toLocaleString()}
                            </p>
                            <p className="text-sm text-gray-500 mt-1">
                                範圍: {results.min_word_count.toLocaleString()} - {results.max_word_count.toLocaleString()}
                            </p>
                        </div>

                        <div className="card">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
                                    <Globe className="w-5 h-5 text-green-600" />
                                </div>
                                <h3 className="font-semibold text-gray-900">競爭對手</h3>
                            </div>
                            <p className="text-3xl font-bold text-gray-900">{results.competitor_count}</p>
                            <p className="text-sm text-gray-500 mt-1">已分析的網站數量</p>
                        </div>

                        <div className="card">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
                                    <FileText className="w-5 h-5 text-purple-600" />
                                </div>
                                <h3 className="font-semibold text-gray-900">常見 H2</h3>
                            </div>
                            <p className="text-3xl font-bold text-gray-900">{results.common_h2_tags.length}</p>
                            <p className="text-sm text-gray-500 mt-1">常見標題結構</p>
                        </div>
                    </div>

                    {/* Keyword Frequency */}
                    {results.keyword_frequency && Object.keys(results.keyword_frequency).length > 0 && (
                        <div className="card">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-orange-50 rounded-lg flex items-center justify-center">
                                    <Hash className="w-5 h-5 text-orange-600" />
                                </div>
                                <h3 className="font-semibold text-gray-900">關鍵字出現頻率</h3>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                {Object.entries(results.keyword_frequency).map(([position, count]) => (
                                    <div key={position} className="text-center p-3 bg-gray-50 rounded-lg">
                                        <p className="text-2xl font-bold text-gray-900">{count}</p>
                                        <p className="text-xs text-gray-500 mt-1 uppercase">{position}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* TF-IDF Keyword Analysis */}
                    {results.tfidf_analysis && results.tfidf_analysis.suggested_keywords.length > 0 && (
                        <div className="card">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg flex items-center justify-center">
                                    <Tags className="w-5 h-5 text-indigo-600" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">TF-IDF 關鍵詞分析</h3>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">從競品提取的高頻關鍵詞建議</p>
                                </div>
                            </div>

                            {/* Keyword Categories */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                                {/* High Frequency */}
                                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                                    <div className="flex items-center gap-2 mb-3">
                                        <TrendingUp className="w-4 h-4 text-blue-600" />
                                        <h4 className="font-medium text-blue-800 dark:text-blue-300">高頻核心詞</h4>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {results.tfidf_analysis.keyword_categories.high_frequency.slice(0, 8).map((kw, i) => (
                                            <span key={i} className="px-2 py-1 bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-200 text-sm rounded-full">
                                                {kw.term}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                {/* Semantic Related */}
                                <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                                    <div className="flex items-center gap-2 mb-3">
                                        <Sparkles className="w-4 h-4 text-green-600" />
                                        <h4 className="font-medium text-green-800 dark:text-green-300">語意相關詞</h4>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {results.tfidf_analysis.keyword_categories.semantic_related.slice(0, 8).map((kw, i) => (
                                            <span key={i} className="px-2 py-1 bg-green-100 dark:bg-green-800 text-green-700 dark:text-green-200 text-sm rounded-full">
                                                {kw.term}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                {/* Long Tail */}
                                <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                                    <div className="flex items-center gap-2 mb-3">
                                        <FileText className="w-4 h-4 text-purple-600" />
                                        <h4 className="font-medium text-purple-800 dark:text-purple-300">長尾關鍵詞</h4>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {results.tfidf_analysis.keyword_categories.long_tail.slice(0, 6).map((kw, i) => (
                                            <span key={i} className="px-2 py-1 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-200 text-sm rounded-full">
                                                {kw.term}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* All Suggested Keywords */}
                            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">所有建議關鍵詞（依重要性排序）</h4>
                                <div className="flex flex-wrap gap-2">
                                    {results.tfidf_analysis.suggested_keywords.slice(0, 20).map((kw, i) => (
                                        <span
                                            key={i}
                                            className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded hover:bg-primary-100 hover:text-primary-700 dark:hover:bg-primary-900 dark:hover:text-primary-300 transition-colors cursor-default"
                                            title={`分數: ${kw.score.toFixed(4)}`}
                                        >
                                            {kw.term}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            {/* Competitor Common Terms */}
                            {results.tfidf_analysis.competitor_common_terms.length > 0 && (
                                <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4">
                                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">競品共同出現詞彙</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {results.tfidf_analysis.competitor_common_terms.slice(0, 15).map((kw, i) => (
                                            <span
                                                key={i}
                                                className="px-2 py-1 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 text-sm rounded-full"
                                            >
                                                {kw.term} <span className="text-xs opacity-70">({kw.count}篇)</span>
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Topic Themes Analysis */}
                    <div className="card">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-semibold text-gray-900">📊 競爭者涵蓋主題</h3>
                            {topicThemes.length === 0 && (
                                <button
                                    onClick={handleAnalyzeThemes}
                                    disabled={isAnalyzingThemes}
                                    className="btn-primary flex items-center gap-2 text-sm py-2 px-4"
                                >
                                    {isAnalyzingThemes ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            分析中...
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles className="w-4 h-4" />
                                            AI 主題分析
                                        </>
                                    )}
                                </button>
                            )}
                        </div>
                        {topicThemes.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {topicThemes.map((theme, index) => (
                                    <div key={index} className="p-4 bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg border border-primary-100">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-medium text-gray-900">{theme.theme_name}</span>
                                            <span className="text-sm bg-primary-600 text-white px-2 py-0.5 rounded-full">
                                                {theme.coverage_count}/{theme.total_competitors} 篇
                                            </span>
                                        </div>
                                        {theme.example_headings.length > 0 && (
                                            <ul className="text-sm text-gray-600 mt-2">
                                                {theme.example_headings.slice(0, 2).map((ex, i) => (
                                                    <li key={i} className="truncate">• {ex}</li>
                                                ))}
                                            </ul>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : !isAnalyzingThemes ? (
                            <p className="text-gray-500 text-sm">
                                點擊「AI 主題分析」按鈕，使用 AI 分析競爭者文章的主題架構
                            </p>
                        ) : null}
                    </div>

                    {/* Competitor List */}
                    <div className="card">
                        <h3 className="font-semibold text-gray-900 mb-4">競爭對手分析</h3>
                        <div className="space-y-3">
                            {results.competitors.map((competitor: CompetitorData) => (
                                <div
                                    key={competitor.rank}
                                    className="border border-gray-200 rounded-lg overflow-hidden"
                                >
                                    <button
                                        onClick={() => toggleCompetitor(competitor.rank)}
                                        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors text-left"
                                    >
                                        <div className="flex items-center gap-4 min-w-0">
                                            <span className="flex-shrink-0 w-8 h-8 bg-primary-50 text-primary-700 rounded-full flex items-center justify-center font-semibold text-sm">
                                                {competitor.rank}
                                            </span>
                                            <div className="min-w-0">
                                                <p className="font-medium text-gray-900 truncate">{competitor.title}</p>
                                                <p className="text-sm text-gray-500 truncate">{competitor.url}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4 flex-shrink-0">
                                            <span className="text-sm text-gray-600">
                                                {competitor.word_count.toLocaleString()} 字
                                            </span>
                                            {expandedCompetitor === competitor.rank ? (
                                                <ChevronUp className="w-5 h-5 text-gray-400" />
                                            ) : (
                                                <ChevronDown className="w-5 h-5 text-gray-400" />
                                            )}
                                        </div>
                                    </button>

                                    {expandedCompetitor === competitor.rank && (
                                        <div className="p-4 pt-0 border-t border-gray-100 bg-gray-50">
                                            {/* H1 Headings */}
                                            {competitor.headings.h1 && competitor.headings.h1.length > 0 && (
                                                <div className="mt-4 p-3 bg-primary-50 rounded-lg">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <Heading1 className="w-4 h-4 text-primary-600" />
                                                        <h4 className="text-sm font-medium text-primary-700">H1 標題</h4>
                                                    </div>
                                                    <ul className="text-sm text-primary-800 space-y-1">
                                                        {competitor.headings.h1.map((h, i) => (
                                                            <li key={i} className="font-medium">• {h}</li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                                                <div>
                                                    <h4 className="text-sm font-medium text-gray-700 mb-2">H2 標題</h4>
                                                    {competitor.headings.h2.length > 0 ? (
                                                        <ul className="text-sm text-gray-600 space-y-1">
                                                            {competitor.headings.h2.map((h, i) => (
                                                                <li key={i}>• {h}</li>
                                                            ))}
                                                        </ul>
                                                    ) : (
                                                        <p className="text-sm text-gray-400">無 H2 標題</p>
                                                    )}
                                                </div>
                                                <div>
                                                    <h4 className="text-sm font-medium text-gray-700 mb-2">H3 標題</h4>
                                                    {competitor.headings.h3.length > 0 ? (
                                                        <ul className="text-sm text-gray-600 space-y-1">
                                                            {competitor.headings.h3.slice(0, 5).map((h, i) => (
                                                                <li key={i}>• {h}</li>
                                                            ))}
                                                            {competitor.headings.h3.length > 5 && (
                                                                <li className="text-gray-400">...還有 {competitor.headings.h3.length - 5} 個</li>
                                                            )}
                                                        </ul>
                                                    ) : (
                                                        <p className="text-sm text-gray-400">無 H3 標題</p>
                                                    )}
                                                </div>
                                            </div>
                                            {competitor.meta_description && (
                                                <div className="mt-4">
                                                    <h4 className="text-sm font-medium text-gray-700 mb-2">Meta 描述</h4>
                                                    <p className="text-sm text-gray-600">{competitor.meta_description}</p>
                                                </div>
                                            )}
                                            {competitor.meta_keywords && (
                                                <div className="mt-4">
                                                    <h4 className="text-sm font-medium text-gray-700 mb-2">Meta 關鍵字</h4>
                                                    <p className="text-sm text-gray-600">{competitor.meta_keywords}</p>
                                                </div>
                                            )}
                                            <div className="mt-4 flex flex-wrap items-center justify-between gap-4">
                                                <a
                                                    href={competitor.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="inline-flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700"
                                                >
                                                    <ExternalLink className="w-4 h-4" />
                                                    在新視窗開啟
                                                </a>
                                                {competitor.scraped_at && (
                                                    <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                                                        <Clock className="w-3 h-3" />
                                                        抓取時間：{new Date(competitor.scraped_at).toLocaleString('zh-TW')}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )
            }

            {/* Empty State */}
            {
                !results && !isLoading && !error && (
                    <div className="card flex flex-col items-center justify-center py-16 text-center">
                        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-6">
                            <Search className="w-10 h-10 text-gray-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            開始你的關鍵字研究
                        </h3>
                        <p className="text-gray-500 max-w-md">
                            輸入目標關鍵字，系統將自動分析 Google 搜尋結果，
                            提供競爭對手分析、字數統計和內容結構建議。
                        </p>
                    </div>
                )
            }
        </div >
    )
}

export default Research
