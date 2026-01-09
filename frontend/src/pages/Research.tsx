import { useState } from 'react'
import { Search, Loader2, Globe, FileText, BarChart3, ExternalLink, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react'
import { researchService, AnalysisReport, CompetitorData } from '../services/research.service'

function Research() {
    const [keyword, setKeyword] = useState('')
    const [market, setMarket] = useState('tw')
    const [isLoading, setIsLoading] = useState(false)
    const [results, setResults] = useState<AnalysisReport | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [expandedCompetitor, setExpandedCompetitor] = useState<number | null>(null)

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!keyword.trim()) return

        setIsLoading(true)
        setError(null)
        setResults(null)

        try {
            const data = await researchService.analyzeKeyword(keyword.trim(), market, 10)
            setResults(data)
        } catch (err: any) {
            const message = err.response?.data?.detail || err.message || '分析失敗，請稍後再試'
            setError(message)
        } finally {
            setIsLoading(false)
        }
    }

    const toggleCompetitor = (rank: number) => {
        setExpandedCompetitor(expandedCompetitor === rank ? null : rank)
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900">關鍵字研究</h1>
                <p className="text-gray-600 mt-1">
                    輸入關鍵字以分析競爭對手和 SERP 結果
                </p>
            </div>

            {/* Search Form */}
            <form onSubmit={handleSearch} className="card">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
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
                    <p className="text-gray-500 text-sm mt-2">這可能需要 30 秒到 1 分鐘</p>
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

                    {/* Common Headings */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="card">
                            <h3 className="font-semibold text-gray-900 mb-4">常見 H2 標題</h3>
                            {results.common_h2_tags.length > 0 ? (
                                <ul className="space-y-2">
                                    {results.common_h2_tags.slice(0, 8).map((tag, index) => (
                                        <li key={index} className="flex items-start gap-2">
                                            <span className="text-primary-600 font-medium text-sm">{index + 1}.</span>
                                            <span className="text-gray-700 text-sm">{tag}</span>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p className="text-gray-500 text-sm">無資料</p>
                            )}
                        </div>

                        <div className="card">
                            <h3 className="font-semibold text-gray-900 mb-4">常見 H3 標題</h3>
                            {results.common_h3_tags.length > 0 ? (
                                <ul className="space-y-2">
                                    {results.common_h3_tags.slice(0, 8).map((tag, index) => (
                                        <li key={index} className="flex items-start gap-2">
                                            <span className="text-primary-600 font-medium text-sm">{index + 1}.</span>
                                            <span className="text-gray-700 text-sm">{tag}</span>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p className="text-gray-500 text-sm">無資料</p>
                            )}
                        </div>
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
                                            <div className="mt-4">
                                                <a
                                                    href={competitor.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="inline-flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700"
                                                >
                                                    <ExternalLink className="w-4 h-4" />
                                                    在新視窗開啟
                                                </a>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}

            {/* Empty State */}
            {!results && !isLoading && !error && (
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
            )}
        </div>
    )
}

export default Research
