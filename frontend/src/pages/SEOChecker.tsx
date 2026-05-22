import { useState } from 'react'
import {
    CheckCircle2, XCircle, AlertCircle, Loader2,
    TrendingUp, Target
} from 'lucide-react'
import api from '../services/api'

interface SEOCheck {
    name: string
    passed: boolean
    score: number
    message: string
    recommendation?: string
}

interface SEOResult {
    overall_score: number
    summary: string
    checks: SEOCheck[]
}

function SEOChecker() {
    const [title, setTitle] = useState('')
    const [content, setContent] = useState('')
    const [keyword, setKeyword] = useState('')
    const [metaDescription, setMetaDescription] = useState('')

    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [result, setResult] = useState<SEOResult | null>(null)
    const [error, setError] = useState<string | null>(null)

    const handleAnalyze = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!title.trim() || !content.trim() || !keyword.trim()) return

        setIsAnalyzing(true)
        setError(null)

        try {
            const response = await api.post<SEOResult>('/seo/analyze', {
                title: title.trim(),
                content: content.trim(),
                keyword: keyword.trim(),
                meta_description: metaDescription.trim(),
            })
            setResult(response.data)
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || '分析失敗')
        } finally {
            setIsAnalyzing(false)
        }
    }

    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-green-600'
        if (score >= 60) return 'text-yellow-600'
        return 'text-red-600'
    }

    const getScoreBg = (score: number) => {
        if (score >= 80) return 'bg-green-50 border-green-200'
        if (score >= 60) return 'bg-yellow-50 border-yellow-200'
        return 'bg-red-50 border-red-200'
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900">SEO 分數檢查器</h1>
                <p className="text-gray-600 mt-1">
                    分析你的文章內容，獲取 SEO 優化建議
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Input Form */}
                <form onSubmit={handleAnalyze} className="card space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            文章標題 *
                        </label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="輸入文章標題"
                            className="input"
                            disabled={isAnalyzing}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            目標關鍵字 *
                        </label>
                        <input
                            type="text"
                            value={keyword}
                            onChange={(e) => setKeyword(e.target.value)}
                            placeholder="輸入目標關鍵字"
                            className="input"
                            disabled={isAnalyzing}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Meta 描述
                        </label>
                        <textarea
                            value={metaDescription}
                            onChange={(e) => setMetaDescription(e.target.value)}
                            placeholder="輸入 Meta 描述 (建議 120-160 字)"
                            className="input"
                            rows={2}
                            disabled={isAnalyzing}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            文章內容 (Markdown) *
                        </label>
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            placeholder="貼上或輸入文章內容..."
                            className="input font-mono text-sm"
                            rows={12}
                            disabled={isAnalyzing}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isAnalyzing || !title.trim() || !content.trim() || !keyword.trim()}
                        className="btn-primary w-full flex items-center justify-center disabled:opacity-50"
                    >
                        {isAnalyzing ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                                分析中...
                            </>
                        ) : (
                            <>
                                <TrendingUp className="w-5 h-5 mr-2" />
                                分析 SEO 分數
                            </>
                        )}
                    </button>
                </form>

                {/* Results */}
                <div className="space-y-6">
                    {error && (
                        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                            {error}
                        </div>
                    )}

                    {result && (
                        <>
                            {/* Overall Score */}
                            <div className={`card border-2 ${getScoreBg(result.overall_score)}`}>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-medium text-gray-600">整體 SEO 分數</p>
                                        <p className={`text-5xl font-bold ${getScoreColor(result.overall_score)}`}>
                                            {result.overall_score}
                                        </p>
                                    </div>
                                    <div className={`w-16 h-16 rounded-full flex items-center justify-center ${result.overall_score >= 80 ? 'bg-green-100' :
                                            result.overall_score >= 60 ? 'bg-yellow-100' : 'bg-red-100'
                                        }`}>
                                        {result.overall_score >= 80 ? (
                                            <CheckCircle2 className="w-8 h-8 text-green-600" />
                                        ) : result.overall_score >= 60 ? (
                                            <AlertCircle className="w-8 h-8 text-yellow-600" />
                                        ) : (
                                            <XCircle className="w-8 h-8 text-red-600" />
                                        )}
                                    </div>
                                </div>
                                <p className="text-gray-600 mt-2">{result.summary}</p>
                            </div>

                            {/* Check Details */}
                            <div className="card">
                                <h3 className="font-semibold text-gray-900 mb-4">詳細檢查結果</h3>
                                <div className="space-y-4">
                                    {result.checks.map((check, index) => (
                                        <div
                                            key={index}
                                            className={`p-4 rounded-lg border ${check.passed ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                                                }`}
                                        >
                                            <div className="flex items-start justify-between">
                                                <div className="flex items-start gap-3">
                                                    {check.passed ? (
                                                        <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
                                                    ) : (
                                                        <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
                                                    )}
                                                    <div>
                                                        <p className="font-medium text-gray-900">{check.name}</p>
                                                        <p className="text-sm text-gray-600 mt-1">{check.message}</p>
                                                        {check.recommendation && (
                                                            <p className="text-sm text-primary-600 mt-2">
                                                                💡 {check.recommendation}
                                                            </p>
                                                        )}
                                                    </div>
                                                </div>
                                                <span className={`text-sm font-medium ${getScoreColor(check.score)}`}>
                                                    {check.score}分
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </>
                    )}

                    {!result && !isAnalyzing && !error && (
                        <div className="card flex flex-col items-center justify-center py-16 text-center">
                            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                                <Target className="w-8 h-8 text-gray-400" />
                            </div>
                            <h3 className="font-medium text-gray-900 mb-2">輸入內容開始分析</h3>
                            <p className="text-gray-500 text-sm">
                                填寫左側表單後點擊分析按鈕
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default SEOChecker
