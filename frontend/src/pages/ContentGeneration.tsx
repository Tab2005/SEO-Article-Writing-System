import { useState, useCallback } from 'react'
import {
    FileText, Loader2, Sparkles, Copy, Check, Download,
    ChevronDown, ChevronUp, Settings2, X, Plus, Edit2, GripVertical,
    ArrowRight, RotateCcw, FileCode
} from 'lucide-react'
import { contentService, ContentResponse } from '../services/content.service'
import { ArticleOutline, OutlineSection } from '../types/content.types'

// Types for editable outline
interface EditableSection {
    id: string
    heading: string
    level: number
    key_points: string[]
}

function ContentGeneration() {
    // Form state
    const [topic, setTopic] = useState('')
    const [keyword, setKeyword] = useState('')
    const [secondaryKeywords, setSecondaryKeywords] = useState<string[]>([])
    const [secondaryInput, setSecondaryInput] = useState('')
    const [wordCount, setWordCount] = useState(2000)
    const [tone, setTone] = useState('professional')
    const [market, setMarket] = useState('tw')
    const [showAdvanced, setShowAdvanced] = useState(false)

    // Workflow state: idle -> outline -> editing -> content -> complete
    const [workflowStep, setWorkflowStep] = useState<'idle' | 'generating-outline' | 'editing-outline' | 'generating-content' | 'complete'>('idle')
    const [outline, setOutline] = useState<ArticleOutline | null>(null)
    const [editableSections, setEditableSections] = useState<EditableSection[]>([])
    const [editableTitle, setEditableTitle] = useState('')
    const [editableMeta, setEditableMeta] = useState('')
    const [result, setResult] = useState<ContentResponse | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [copied, setCopied] = useState(false)

    // Editing state
    const [editingIndex, setEditingIndex] = useState<number | null>(null)
    const [dragIndex, setDragIndex] = useState<number | null>(null)

    // Secondary keywords handlers
    const addSecondaryKeyword = () => {
        const trimmed = secondaryInput.trim()
        if (trimmed && !secondaryKeywords.includes(trimmed) && secondaryKeywords.length < 10) {
            setSecondaryKeywords([...secondaryKeywords, trimmed])
            setSecondaryInput('')
        }
    }

    const removeSecondaryKeyword = (kw: string) => {
        setSecondaryKeywords(secondaryKeywords.filter(k => k !== kw))
    }

    const handleSecondaryKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault()
            addSecondaryKeyword()
        }
    }

    // Step 1: Generate outline only
    const handleGenerateOutline = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!topic.trim() || !keyword.trim()) return

        setWorkflowStep('generating-outline')
        setError(null)
        setOutline(null)
        setResult(null)

        try {
            const outlineData = await contentService.generateOutline({
                topic: topic.trim(),
                target_keyword: keyword.trim(),
                secondary_keywords: secondaryKeywords,
                word_count_target: wordCount,
                tone,
                market,
                use_competitor_analysis: true,
            })
            setOutline(outlineData)
            setEditableTitle(outlineData.title)
            setEditableMeta(outlineData.meta_description)
            setEditableSections(
                outlineData.sections.map((s, i) => ({
                    id: `section-${i}`,
                    heading: s.heading,
                    level: s.level,
                    key_points: s.key_points,
                }))
            )
            setWorkflowStep('editing-outline')
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || '大綱生成失敗')
            setWorkflowStep('idle')
        }
    }

    // Step 2: Generate content from edited outline
    const handleGenerateContent = async () => {
        setWorkflowStep('generating-content')
        setError(null)

        try {
            const data = await contentService.generateContent({
                topic: editableTitle,
                target_keyword: keyword.trim(),
                secondary_keywords: secondaryKeywords,
                word_count_target: wordCount,
                tone,
                market,
            })
            setResult(data)
            setWorkflowStep('complete')
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || '內容生成失敗')
            setWorkflowStep('editing-outline')
        }
    }

    // Outline editing handlers
    const updateSectionHeading = (index: number, heading: string) => {
        const updated = [...editableSections]
        updated[index].heading = heading
        setEditableSections(updated)
    }

    const removeSection = (index: number) => {
        setEditableSections(editableSections.filter((_, i) => i !== index))
    }

    const addSection = () => {
        setEditableSections([
            ...editableSections,
            {
                id: `section-${Date.now()}`,
                heading: '新段落標題',
                level: 2,
                key_points: [],
            },
        ])
    }

    // Drag and drop handlers
    const handleDragStart = (index: number) => {
        setDragIndex(index)
    }

    const handleDragOver = (e: React.DragEvent, index: number) => {
        e.preventDefault()
        if (dragIndex === null || dragIndex === index) return

        const updated = [...editableSections]
        const [dragged] = updated.splice(dragIndex, 1)
        updated.splice(index, 0, dragged)
        setEditableSections(updated)
        setDragIndex(index)
    }

    const handleDragEnd = () => {
        setDragIndex(null)
    }

    // Reset to start over
    const resetWorkflow = () => {
        setWorkflowStep('idle')
        setOutline(null)
        setEditableSections([])
        setResult(null)
        setError(null)
    }

    // Copy and download handlers
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

    const downloadHTML = () => {
        if (!result?.content) return
        // Simple markdown to HTML conversion
        let html = result.content
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p>')

        const fullHtml = `<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="${result.outline.meta_description}">
    <title>${result.outline.title}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; line-height: 1.6; }
        h1, h2, h3 { color: #1a1a1a; margin-top: 2rem; }
        p { color: #333; }
    </style>
</head>
<body>
<p>${html}</p>
</body>
</html>`

        const blob = new Blob([fullHtml], { type: 'text/html' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${keyword.replace(/\s+/g, '-')}.html`
        a.click()
        URL.revokeObjectURL(url)
    }

    const isLoading = workflowStep === 'generating-outline' || workflowStep === 'generating-content'

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">AI 內容生成</h1>
                    <p className="text-gray-600 mt-1">
                        {workflowStep === 'idle' && '輸入主題和關鍵字，AI 將自動生成 SEO 優化的文章'}
                        {workflowStep === 'generating-outline' && '正在分析競品並生成大綱...'}
                        {workflowStep === 'editing-outline' && '編輯大綱結構，確認後開始撰寫'}
                        {workflowStep === 'generating-content' && '正在根據大綱撰寫文章...'}
                        {workflowStep === 'complete' && '文章生成完成！'}
                    </p>
                </div>
                {(workflowStep === 'editing-outline' || workflowStep === 'complete') && (
                    <button
                        onClick={resetWorkflow}
                        className="btn-secondary flex items-center gap-2"
                    >
                        <RotateCcw className="w-4 h-4" />
                        重新開始
                    </button>
                )}
            </div>

            {/* Step 1: Input Form */}
            {workflowStep === 'idle' && (
                <form onSubmit={handleGenerateOutline} className="card space-y-6">
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
                            />
                        </div>
                    </div>

                    {/* Secondary Keywords */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            次要關鍵字 (選填，最多 10 個)
                        </label>
                        <div className="flex flex-wrap gap-2 mb-2">
                            {secondaryKeywords.map((kw, i) => (
                                <span
                                    key={i}
                                    className="inline-flex items-center gap-1 px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm"
                                >
                                    {kw}
                                    <button
                                        type="button"
                                        onClick={() => removeSecondaryKeyword(kw)}
                                        className="hover:text-primary-900"
                                    >
                                        <X className="w-3 h-3" />
                                    </button>
                                </span>
                            ))}
                        </div>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={secondaryInput}
                                onChange={(e) => setSecondaryInput(e.target.value)}
                                onKeyPress={handleSecondaryKeyPress}
                                placeholder="輸入次要關鍵字後按 Enter 新增"
                                className="input flex-1"
                                disabled={secondaryKeywords.length >= 10}
                            />
                            <button
                                type="button"
                                onClick={addSecondaryKeyword}
                                className="btn-secondary flex items-center gap-1 py-2 px-3"
                                disabled={!secondaryInput.trim() || secondaryKeywords.length >= 10}
                            >
                                <Plus className="w-4 h-4" />
                                新增
                            </button>
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
                        disabled={!topic.trim() || !keyword.trim()}
                        className="btn-primary flex items-center justify-center w-full md:w-auto disabled:opacity-50"
                    >
                        <Sparkles className="w-5 h-5 mr-2" />
                        生成文章大綱
                    </button>
                </form>
            )}

            {/* Loading State */}
            {isLoading && (
                <div className="card flex flex-col items-center justify-center py-16">
                    <Loader2 className="w-12 h-12 text-primary-600 animate-spin mb-4" />
                    <p className="text-lg font-medium text-gray-900">
                        {workflowStep === 'generating-outline' ? '正在分析競品並生成大綱...' : '正在撰寫文章內容...'}
                    </p>
                    <p className="text-gray-500 text-sm mt-2">這可能需要 1-2 分鐘</p>
                </div>
            )}

            {/* Error */}
            {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                    {error}
                </div>
            )}

            {/* Step 2: Edit Outline */}
            {workflowStep === 'editing-outline' && outline && (
                <div className="space-y-6">
                    <div className="card">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-lg font-semibold text-gray-900">編輯文章大綱</h2>
                            <span className="text-sm text-gray-500">
                                拖拽調整順序，點擊編輯標題
                            </span>
                        </div>

                        {/* Title and Meta */}
                        <div className="space-y-4 mb-6 p-4 bg-primary-50 rounded-lg">
                            <div>
                                <label className="block text-sm font-medium text-primary-700 mb-1">
                                    文章標題
                                </label>
                                <input
                                    type="text"
                                    value={editableTitle}
                                    onChange={(e) => setEditableTitle(e.target.value)}
                                    className="input bg-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-primary-700 mb-1">
                                    Meta 描述
                                </label>
                                <textarea
                                    value={editableMeta}
                                    onChange={(e) => setEditableMeta(e.target.value)}
                                    className="input bg-white"
                                    rows={2}
                                />
                            </div>
                        </div>

                        {/* Sections */}
                        <div className="space-y-2">
                            {editableSections.map((section, index) => (
                                <div
                                    key={section.id}
                                    draggable
                                    onDragStart={() => handleDragStart(index)}
                                    onDragOver={(e) => handleDragOver(e, index)}
                                    onDragEnd={handleDragEnd}
                                    className={`flex items-center gap-3 p-3 border rounded-lg cursor-move transition-colors ${dragIndex === index ? 'bg-primary-50 border-primary-300' : 'bg-white border-gray-200 hover:border-gray-300'
                                        }`}
                                >
                                    <GripVertical className="w-5 h-5 text-gray-400 flex-shrink-0" />
                                    <span className="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0">
                                        H{section.level}
                                    </span>
                                    {editingIndex === index ? (
                                        <input
                                            type="text"
                                            value={section.heading}
                                            onChange={(e) => updateSectionHeading(index, e.target.value)}
                                            onBlur={() => setEditingIndex(null)}
                                            onKeyPress={(e) => e.key === 'Enter' && setEditingIndex(null)}
                                            className="input flex-1"
                                            autoFocus
                                        />
                                    ) : (
                                        <span
                                            className="flex-1 text-gray-700 cursor-text"
                                            onClick={() => setEditingIndex(index)}
                                        >
                                            {section.heading}
                                        </span>
                                    )}
                                    <button
                                        onClick={() => setEditingIndex(editingIndex === index ? null : index)}
                                        className="p-1 text-gray-400 hover:text-gray-600"
                                    >
                                        <Edit2 className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => removeSection(index)}
                                        className="p-1 text-gray-400 hover:text-red-600"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                        </div>

                        {/* Add Section Button */}
                        <button
                            type="button"
                            onClick={addSection}
                            className="mt-4 w-full p-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-primary-300 hover:text-primary-600 transition-colors flex items-center justify-center gap-2"
                        >
                            <Plus className="w-4 h-4" />
                            新增段落
                        </button>

                        {/* Confirm Button */}
                        <div className="mt-6 pt-6 border-t border-gray-200 flex justify-end">
                            <button
                                onClick={handleGenerateContent}
                                className="btn-primary flex items-center gap-2"
                            >
                                確認大綱，開始撰寫
                                <ArrowRight className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Step 3: Complete - Show Result */}
            {workflowStep === 'complete' && result && (
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
                                <button
                                    onClick={downloadHTML}
                                    className="btn-secondary flex items-center gap-2 text-sm py-2"
                                >
                                    <FileCode className="w-4 h-4" />
                                    下載 HTML
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
            {workflowStep === 'idle' && !error && (
                <div className="card flex flex-col items-center justify-center py-16 text-center">
                    <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-6">
                        <FileText className="w-10 h-10 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        開始生成 SEO 文章
                    </h3>
                    <p className="text-gray-500 max-w-md">
                        輸入文章主題和目標關鍵字，AI 將分析競品後生成優化的文章大綱。
                        您可以編輯大綱後再生成完整內容。
                    </p>
                </div>
            )}
        </div>
    )
}

export default ContentGeneration
