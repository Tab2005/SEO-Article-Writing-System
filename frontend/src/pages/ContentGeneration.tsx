import { useState } from 'react'
import {
    FileText, Loader2, Sparkles, Copy, Check, Download,
    ChevronDown, ChevronUp, Settings2
} from 'lucide-react'
import { contentService, ContentResponse } from '../services/content.service'
import { ArticleOutline } from '../types/content.types'

function ContentGeneration() {
    const [topic, setTopic] = useState('')
    const [keyword, setKeyword] = useState('')
    const [wordCount, setWordCount] = useState(2000)
    const [tone, setTone] = useState('professional')
    const [market, setMarket] = useState('tw')
    const [showAdvanced, setShowAdvanced] = useState(false)

    const [isGenerating, setIsGenerating] = useState(false)
    const [step, setStep] = useState<'idle' | 'outline' | 'content'>('idle')
    const [result, setResult] = useState<ContentResponse | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [copied, setCopied] = useState(false)

    const handleGenerate = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!topic.trim() || !keyword.trim()) return

        setIsGenerating(true)
        setError(null)
        setResult(null)
        setStep('outline')

        try {
            setStep('content')
            const data = await contentService.generateContent({
                topic: topic.trim(),
                target_keyword: keyword.trim(),
                word_count_target: wordCount,
                tone,
                market,
            })
            setResult(data)
            setStep('idle')
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || '生成失敗')
            setStep('idle')
        } finally {
            setIsGenerating(false)
        }
    }

    const copyToClipboard = async () => {
        if (!result?.content) return
        await navigator.clipboard.writeText(result.content)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const downloadMarkdown = () => {
        if (!result?.content) return
        const blob = new Blob([result.content], { type: 'text/markdown' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${keyword.replace(/\s+/g, '-')}.md`
        a.click()
        URL.revokeObjectURL(url)
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900">AI 內容生成</h1>
                <p className="text-gray-600 mt-1">
                    輸入主題和關鍵字，AI 將自動生成 SEO 優化的文章
                </p>
            </div>

            {/* Form */}
            <form onSubmit={handleGenerate} className="card space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            文章主題 *
                        </label>
                        <input
                            type="text"
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            placeholder="例如：如何製作完美的義大利麵"
                            className="input"
                            disabled={isGenerating}
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
                            placeholder="例如：義大利麵做法"
                            className="input"
                            disabled={isGenerating}
                        />
                    </div>
                </div>

                {/* Advanced Options */}
                <div>
                    <button
                        type="button"
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
                    >
                        <Settings2 className="w-4 h-4" />
                        進階選項
                        {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>

                    {showAdvanced && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 p-4 bg-gray-50 rounded-lg">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    目標字數
                                </label>
                                <select
                                    value={wordCount}
                                    onChange={(e) => setWordCount(Number(e.target.value))}
                                    className="input"
                                    disabled={isGenerating}
                                >
                                    <option value={1000}>1000 字</option>
                                    <option value={1500}>1500 字</option>
                                    <option value={2000}>2000 字</option>
                                    <option value={3000}>3000 字</option>
                                    <option value={5000}>5000 字</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    文章風格
                                </label>
                                <select
                                    value={tone}
                                    onChange={(e) => setTone(e.target.value)}
                                    className="input"
                                    disabled={isGenerating}
                                >
                                    <option value="professional">專業嚴謹</option>
                                    <option value="friendly">親切友善</option>
                                    <option value="casual">輕鬆隨意</option>
                                    <option value="academic">學術正式</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    目標市場
                                </label>
                                <select
                                    value={market}
                                    onChange={(e) => setMarket(e.target.value)}
                                    className="input"
                                    disabled={isGenerating}
                                >
                                    <option value="tw">台灣</option>
                                    <option value="hk">香港</option>
                                    <option value="us">美國</option>
                                </select>
                            </div>
                        </div>
                    )}
                </div>

                <button
                    type="submit"
                    disabled={isGenerating || !topic.trim() || !keyword.trim()}
                    className="btn-primary flex items-center justify-center w-full md:w-auto disabled:opacity-50"
                >
                    {isGenerating ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin mr-2" />
                            {step === 'outline' ? '生成大綱中...' : '撰寫內容中...'}
                        </>
                    ) : (
                        <>
                            <Sparkles className="w-5 h-5 mr-2" />
                            開始生成文章
                        </>
                    )}
                </button>
            </form>

            {/* Error */}
            {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                    {error}
                </div>
            )}

            {/* Loading */}
            {isGenerating && (
                <div className="card flex flex-col items-center justify-center py-16">
                    <Loader2 className="w-12 h-12 text-primary-600 animate-spin mb-4" />
                    <p className="text-lg font-medium text-gray-900">
                        {step === 'outline' ? '正在分析競品並生成大綱...' : '正在撰寫文章內容...'}
                    </p>
                    <p className="text-gray-500 text-sm mt-2">這可能需要 1-2 分鐘</p>
                </div>
            )}

            {/* Result */}
            {result && !isGenerating && (
                <div className="space-y-6">
                    {/* Outline Preview */}
                    <div className="card">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-gray-900">文章大綱</h2>
                            <span className="text-sm text-gray-500">
                                預估 {result.outline.estimated_word_count.toLocaleString()} 字
                            </span>
                        </div>
                        <div className="space-y-2">
                            <h3 className="font-medium text-primary-700">{result.outline.title}</h3>
                            <p className="text-sm text-gray-600">{result.outline.meta_description}</p>
                            <ul className="mt-4 space-y-1 text-sm text-gray-700">
                                {result.outline.sections.map((section, i) => (
                                    <li key={i} className="flex items-start gap-2">
                                        <span className="text-primary-500">•</span>
                                        {section.heading}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="card">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-gray-900">生成的文章</h2>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={copyToClipboard}
                                    className="btn-secondary flex items-center gap-2 text-sm py-2"
                                >
                                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                    {copied ? '已複製' : '複製'}
                                </button>
                                <button
                                    onClick={downloadMarkdown}
                                    className="btn-secondary flex items-center gap-2 text-sm py-2"
                                >
                                    <Download className="w-4 h-4" />
                                    下載 MD
                                </button>
                            </div>
                        </div>
                        <div className="prose prose-sm max-w-none">
                            <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
                                {result.content}
                            </pre>
                        </div>
                        <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-500">
                            實際字數: {result.word_count.toLocaleString()} 字
                        </div>
                    </div>
                </div>
            )}

            {/* Empty State */}
            {!result && !isGenerating && !error && (
                <div className="card flex flex-col items-center justify-center py-16 text-center">
                    <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-6">
                        <FileText className="w-10 h-10 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        開始生成 SEO 文章
                    </h3>
                    <p className="text-gray-500 max-w-md">
                        輸入文章主題和目標關鍵字，AI 將分析競品後自動生成
                        優化的文章大綱和完整內容。
                    </p>
                </div>
            )}
        </div>
    )
}

export default ContentGeneration
