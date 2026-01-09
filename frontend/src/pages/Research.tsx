import { useState } from 'react'
import { Search, Loader2, Globe, FileText, BarChart3 } from 'lucide-react'

function Research() {
    const [keyword, setKeyword] = useState('')
    const [market, setMarket] = useState('tw')
    const [isLoading, setIsLoading] = useState(false)
    const [results, setResults] = useState<any>(null)
    const [error, setError] = useState<string | null>(null)

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!keyword.trim()) return

        setIsLoading(true)
        setError(null)

        try {
            // API call will be implemented when backend is running
            // For now, show a placeholder
            setResults({ placeholder: true })
        } catch (err: any) {
            setError(err.response?.data?.detail || '搜尋失敗')
        } finally {
            setIsLoading(false)
        }
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
                            className="btn-primary w-full md:w-auto disabled:opacity-50"
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
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                    {error}
                </div>
            )}

            {/* Results Placeholder */}
            {results && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Stats */}
                    <div className="card">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                                <BarChart3 className="w-5 h-5 text-blue-600" />
                            </div>
                            <h3 className="font-semibold text-gray-900">平均字數</h3>
                        </div>
                        <p className="text-3xl font-bold text-gray-900">--</p>
                        <p className="text-sm text-gray-500 mt-1">競爭對手平均字數</p>
                    </div>

                    <div className="card">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
                                <Globe className="w-5 h-5 text-green-600" />
                            </div>
                            <h3 className="font-semibold text-gray-900">競爭對手</h3>
                        </div>
                        <p className="text-3xl font-bold text-gray-900">--</p>
                        <p className="text-sm text-gray-500 mt-1">已分析的網站數量</p>
                    </div>

                    <div className="card">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
                                <FileText className="w-5 h-5 text-purple-600" />
                            </div>
                            <h3 className="font-semibold text-gray-900">常見 H2</h3>
                        </div>
                        <p className="text-3xl font-bold text-gray-900">--</p>
                        <p className="text-sm text-gray-500 mt-1">常見標題結構</p>
                    </div>
                </div>
            )}

            {/* Empty State */}
            {!results && !isLoading && (
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
