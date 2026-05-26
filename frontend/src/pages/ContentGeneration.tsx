import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
    FileText, Loader2, Sparkles, Copy, Check, Download,
    ChevronDown, ChevronUp, Settings2, X, Plus, Edit2, GripVertical,
    ArrowRight, RotateCcw, FileCode, BookOpen, AlertCircle,
    CheckCircle2, AlertTriangle, ShieldCheck, ShieldAlert
} from 'lucide-react'
import { contentService, ContentResponse } from '../services/content.service'
import { ArticleOutline } from '../types/content.types'
import { useProjectStore } from '../store/projectStore'
import { planningService, ArticleBrief, TopicNode } from '../services/planning.service'
import { draftService } from '../services/draft.service'

// Types for editable outline
interface EditableSection {
    id: string
    heading: string
    level: number
    key_points: string[]
}

function ContentGeneration() {
    const navigate = useNavigate()
    const [searchParams] = useSearchParams()
    const briefIdParam = searchParams.get('brief_id')
    const { currentProject } = useProjectStore()

    // Form state
    const [topic, setTopic] = useState('')
    const [keyword, setKeyword] = useState('')
    const [secondaryKeywords, setSecondaryKeywords] = useState<string[]>([])
    const [secondaryInput, setSecondaryInput] = useState('')
    const [wordCount, setWordCount] = useState(2000)
    const [tone, setTone] = useState('professional')
    const [market, setMarket] = useState('tw')
    const [showAdvanced, setShowAdvanced] = useState(false)

    // Brief states
    const [briefs, setBriefs] = useState<ArticleBrief[]>([])
    const [topicNodes, setTopicNodes] = useState<TopicNode[]>([])
    const [selectedBriefId, setSelectedBriefId] = useState('')
    const [selectedBrief, setSelectedBrief] = useState<ArticleBrief | null>(null)

    useEffect(() => {
        if (!currentProject) return
        loadBriefsAndTopics()
    }, [currentProject])

    const loadBriefsAndTopics = async () => {
        if (!currentProject) return
        try {
            const [briefList, nodeList] = await Promise.all([
                planningService.listBriefs(currentProject.id),
                planningService.getTopicNodes(currentProject.id)
            ])
            const approvedBriefs = briefList.filter(b => b.status === 'approved')
            setBriefs(approvedBriefs)
            setTopicNodes(nodeList)

            // 自動選取 brief_id 參數
            if (briefIdParam) {
                const foundBrief = approvedBriefs.find(b => b.id === briefIdParam)
                if (foundBrief) {
                    setSelectedBriefId(briefIdParam)
                    setSelectedBrief(foundBrief)
                    setTopic(foundBrief.title_direction)
                    
                    if (foundBrief.mapped_topic_id) {
                        const node = nodeList.find(n => n.id === foundBrief.mapped_topic_id)
                        if (node) {
                            setKeyword(node.name)
                        } else {
                            setKeyword('')
                        }
                    } else {
                        setKeyword('')
                    }
                }
            }
        } catch (err) {
            console.error('Failed to load briefs in ContentGeneration:', err)
        }
    }

    const handleBriefChange = (briefId: string) => {
        setSelectedBriefId(briefId)
        if (!briefId) {
            setSelectedBrief(null)
            setTopic('')
            setKeyword('')
            return
        }

        const foundBrief = briefs.find(b => b.id === briefId)
        if (foundBrief) {
            setSelectedBrief(foundBrief)
            setTopic(foundBrief.title_direction)
            
            if (foundBrief.mapped_topic_id) {
                const node = topicNodes.find(n => n.id === foundBrief.mapped_topic_id)
                if (node) {
                    setKeyword(node.name)
                } else {
                    setKeyword('')
                }
            } else {
                setKeyword('')
            }
        }
    }

    // Workflow state: idle -> outline -> editing -> content -> complete
    const [workflowStep, setWorkflowStep] = useState<'idle' | 'generating-outline' | 'editing-outline' | 'generating-content' | 'complete'>('idle')
    const [outline, setOutline] = useState<ArticleOutline | null>(null)
    const [editableSections, setEditableSections] = useState<EditableSection[]>([])
    const [editableTitle, setEditableTitle] = useState('')
    const [editableMeta, setEditableMeta] = useState('')
    const [result, setResult] = useState<ContentResponse | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [copied, setCopied] = useState(false)
    const [createdDraftId, setCreatedDraftId] = useState<string | null>(null)
    const [qaStatus, setQaStatus] = useState<'idle' | 'running' | 'success' | 'error'>('idle')
    const [qaResult, setQaResult] = useState<any>(null)
    const [qaError, setQaError] = useState<string | null>(null)

    // Editing state
    const [editingIndex, setEditingIndex] = useState<number | null>(null)
    const [dragIndex, setDragIndex] = useState<number | null>(null)

    // Versioning states
    const [versions, setVersions] = useState<any[]>([])
    const [loadingVersions, setLoadingVersions] = useState(false)
    const [showVersionsModal, setShowVersionsModal] = useState(false)

    const loadVersions = async (draftId: string) => {
        setLoadingVersions(true)
        try {
            const list = await contentService.getDraftVersions(draftId)
            setVersions(list)
        } catch (err) {
            console.error('Failed to load draft versions:', err)
        } finally {
            setLoadingVersions(false)
        }
    }

    useEffect(() => {
        if (createdDraftId) {
            loadVersions(createdDraftId)
        }
    }, [createdDraftId])

    const handleSaveVersion = async () => {
        if (!createdDraftId) return
        try {
            await contentService.saveNewVersion(createdDraftId)
            await loadVersions(createdDraftId)
            alert('手動保存版本成功！')
        } catch (err: any) {
            alert(err.response?.data?.detail || err.message || '手動保存版本失敗')
        }
    }

    const handleRollback = async (versionId: string) => {
        if (!createdDraftId) return
        if (!window.confirm('確定要還原到此版本嗎？目前編輯器中的未保存修改將會被覆蓋。')) return
        try {
            const updatedDraft = await contentService.rollbackVersion(createdDraftId, versionId)
            if (result && updatedDraft) {
                setResult({
                    ...result,
                    content: updatedDraft.content || '',
                    word_count: updatedDraft.word_count || 0
                })
            }
            await loadVersions(createdDraftId)
            setShowVersionsModal(false)
            alert('版本已成功還原！')
        } catch (err: any) {
            alert(err.response?.data?.detail || err.message || '還原版本失敗')
        }
    }

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
        if (!topic.trim() || !keyword.trim() || !selectedBriefId) {
            alert('請選擇文章任務書並確保主題與關鍵字已填寫。')
            return
        }

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
                brief_id: selectedBriefId
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
        if (!selectedBriefId) {
            alert('請先選擇已核准的文章任務書。')
            return
        }

        setWorkflowStep('generating-content')
        setError(null)
        setCreatedDraftId(null)
        setQaStatus('idle')
        setQaResult(null)
        setQaError(null)

        const outlineObj = {
            title: editableTitle,
            meta_description: editableMeta,
            sections: editableSections.map(s => ({
                heading: s.heading,
                level: s.level,
                key_points: s.key_points || [],
                subsections: []
            })),
            estimated_word_count: wordCount,
            target_keywords: [keyword.trim(), ...(secondaryKeywords || [])]
        }

        try {
            const data = await contentService.generateContent({
                topic: editableTitle,
                target_keyword: keyword.trim(),
                secondary_keywords: secondaryKeywords,
                word_count_target: wordCount,
                tone,
                market,
                brief_id: selectedBriefId,
                outline: outlineObj
            })
            setResult(data)
            setWorkflowStep('complete')

            // 背景自動保存為草稿 (Draft) 以供後續 QA 審查
            if (currentProject) {
                try {
                    const draft = await draftService.createDraft({
                        project_id: currentProject.id,
                        keyword: keyword.trim(),
                        title: editableTitle,
                        wizard_step: 4,
                        brief_id: selectedBriefId || undefined,
                        outline: outlineObj
                    })
                    await draftService.updateDraft(draft.id, {
                        content: data.content,
                        word_count: data.word_count,
                        status: 'draft'
                    })
                    setCreatedDraftId(draft.id)
                } catch (saveErr) {
                    console.error('背景自動保存草稿失敗:', saveErr)
                }
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || '內容生成失敗')
            setWorkflowStep('editing-outline')
        }
    }

    // Step 4: Run QA Gate Auditor
    const handleRunQA = async () => {
        if (!createdDraftId) return
        setQaStatus('running')
        setQaError(null)
        try {
            const data = await contentService.runQA(createdDraftId)
            setQaResult(data.qa_results)
            setQaStatus('success')
        } catch (err: any) {
            setQaError(err.response?.data?.detail || err.message || 'QA 審查失敗')
            setQaStatus('error')
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

    if (!currentProject) {
        return (
            <div className="card text-center py-16 flex flex-col items-center justify-center">
                <BookOpen className="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">未選定專案</h3>
                <p className="text-gray-500 dark:text-gray-400">請先在左上角選擇或建立一個專案以使用內容生成功能！</p>
            </div>
        )
    }

    const isLoading = workflowStep === 'generating-outline' || workflowStep === 'generating-content'

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">AI 內容生成</h1>
                    <p className="text-gray-600 mt-1">
                        {workflowStep === 'idle' && '選取已核准的任務書以自動套用 SEO 與品牌策略進行寫作'}
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
                <div className="space-y-6">
                    {briefs.length === 0 ? (
                        <div className="card border-dashed border-red-200 dark:border-red-950/40 p-8 text-center flex flex-col items-center justify-center bg-red-50/20 dark:bg-red-950/10">
                            <AlertCircle className="w-12 h-12 text-red-500 mb-3" />
                            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">無可用文章任務書 (No Approved Briefs)</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400 max-w-md mb-6 leading-relaxed">
                                本系統實施「Brief-First」流程。您必須先在「題目評估」或「文章任務書」模組中，建立並將任務書狀態核准為 <strong>已核准 (Approved)</strong>，方能解鎖 AI 文章寫作。
                            </p>
                            <button
                                onClick={() => navigate('/briefs')}
                                className="btn btn-primary flex items-center gap-2"
                            >
                                前往文章任務書管理 <ArrowRight className="w-4 h-4" />
                            </button>
                        </div>
                    ) : (
                        <form onSubmit={handleGenerateOutline} className="card space-y-6">
                            {/* Brief Selector */}
                            <div className="p-5 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-gray-100 dark:border-slate-800 space-y-4">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2 flex items-center gap-1.5">
                                        <FileText className="w-4.5 h-4.5 text-primary-600" />
                                        選擇已核准的文章任務書 *
                                    </label>
                                    <select
                                        value={selectedBriefId}
                                        onChange={(e) => handleBriefChange(e.target.value)}
                                        required
                                        className="w-full rounded-lg border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100 focus:ring-primary-500"
                                    >
                                        <option value="">-- 請選擇文章任務書 (核准狀態) --</option>
                                        {briefs.map(b => (
                                            <option key={b.id} value={b.id}>
                                                {b.title_direction} (更新於 {new Date(b.updated_at).toLocaleDateString('zh-TW')})
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                {selectedBrief && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 text-xs border-t border-gray-100 dark:border-slate-800">
                                        <div className="space-y-1">
                                            <span className="font-bold text-gray-500">目標讀者：</span>
                                            <p className="text-gray-700 dark:text-gray-300 font-medium leading-relaxed">{selectedBrief.target_audience || '未指定'}</p>
                                        </div>
                                        <div className="space-y-1">
                                            <span className="font-bold text-gray-500">核心解答問題：</span>
                                            <p className="text-gray-700 dark:text-gray-300 font-medium leading-relaxed">{selectedBrief.primary_question || '未指定'}</p>
                                        </div>
                                        <div className="space-y-1">
                                            <span className="font-bold text-gray-500">資訊增益要求：</span>
                                            <p className="text-gray-700 dark:text-gray-300 font-medium leading-relaxed">{selectedBrief.info_gain_requirement || '未指定'}</p>
                                        </div>
                                        <div className="space-y-1">
                                            <span className="font-bold text-red-500">禁用與邊界內容：</span>
                                            <p className="text-red-600/90 dark:text-red-400 font-medium leading-relaxed">{selectedBrief.restricted_content || '無'}</p>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        文章主題 * (依任務書鎖定)
                                    </label>
                                    <input
                                        type="text"
                                        value={topic}
                                        readOnly
                                        placeholder="請先在上方選取文章任務書"
                                        className="input bg-gray-50 dark:bg-slate-900 border-gray-200 dark:border-slate-800 cursor-not-allowed text-gray-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        目標關鍵字 * (依主題自動帶入)
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
        </div>
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

                    {/* QA Gate V1 Card */}
                    <div className="card border border-gray-100 bg-white/80 backdrop-blur-md shadow-sm relative overflow-hidden transition-all duration-300">
                        {/* HSL Gradient Top Bar */}
                        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />
                        
                        <div className="flex items-center justify-between mb-4 mt-1">
                            <div className="flex items-center gap-2">
                                <Sparkles className="w-5 h-5 text-indigo-500" />
                                <h2 className="text-lg font-semibold text-gray-900">AI 品質審查 (QA Gate V1)</h2>
                            </div>
                            
                            {/* Status Badge */}
                            {qaStatus === 'success' && qaResult && (
                                <span className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full ${
                                    qaResult.is_passed 
                                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                                        : 'bg-rose-50 text-rose-700 border border-rose-200'
                                }`}>
                                    {qaResult.is_passed ? <ShieldCheck className="w-3.5 h-3.5" /> : <ShieldAlert className="w-3.5 h-3.5" />}
                                    {qaResult.is_passed ? '通過品質稽核' : '未通過品質稽核'}
                                </span>
                            )}
                        </div>

                        {qaStatus === 'idle' && (
                            <div className="py-6 text-center">
                                <p className="text-sm text-gray-500 mb-4">
                                    此文章已背景備份至草稿。您可以立即執行 AI 品質審查，針對網站定位契合度、禁用詞、資訊增益與 CTA 等四大維度進行合規性稽核。
                                </p>
                                <button
                                    onClick={handleRunQA}
                                    disabled={!createdDraftId}
                                    className="btn-primary inline-flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-medium rounded-lg shadow-sm hover:shadow transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <Sparkles className="w-4 h-4" />
                                    執行 QA 品質稽核
                                </button>
                                {!createdDraftId && (
                                    <p className="text-xs text-rose-500 mt-2">（草稿保存中，請稍候...）</p>
                                )}
                            </div>
                        )}

                        {qaStatus === 'running' && (
                            <div className="py-8 flex flex-col items-center justify-center text-center">
                                <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mb-4" />
                                <h3 className="text-sm font-semibold text-gray-700 mb-1">正在進行 AI 品質稽核...</h3>
                                <p className="text-xs text-gray-500">正在對照網站定位與文章任務書約束進行深度分析</p>
                            </div>
                        )}

                        {qaStatus === 'error' && (
                            <div className="py-6 text-center">
                                <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-3" />
                                <p className="text-sm text-rose-600 font-medium mb-4">{qaError}</p>
                                <button
                                    onClick={handleRunQA}
                                    className="btn-secondary inline-flex items-center gap-2"
                                >
                                    <RotateCcw className="w-4 h-4" />
                                    重新執行審查
                                </button>
                            </div>
                        )}

                        {qaStatus === 'success' && qaResult && (
                            <div className="space-y-4">
                                {qaResult.is_passed ? (
                                    <div className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-lg flex items-start gap-3">
                                        <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                                        <div>
                                            <h4 className="text-sm font-semibold text-emerald-900">恭喜！文章已順利通過全部品質稽核</h4>
                                            <p className="text-xs text-emerald-700 mt-1">
                                                本文章完全符合您的網站定位，且沒有觸碰任何禁用詞或受限主題。資訊增益與 CTA 的比對皆已通過。
                                            </p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="p-4 bg-rose-50/50 border border-rose-100 rounded-lg flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
                                        <div>
                                            <h4 className="text-sm font-semibold text-rose-900">偵測到需要修正的品質問題</h4>
                                            <p className="text-xs text-rose-700 mt-1">
                                                AI 偵測到文章在定位、禁用內容、資訊增益或 CTA 方面有不符規範的內容，請參考下方的具體問題清單與建議進行修改。
                                            </p>
                                        </div>
                                    </div>
                                )}

                                {/* Issues List */}
                                <div className="space-y-3">
                                    <h3 className="text-sm font-semibold text-gray-800">稽核細項與改進建議 ({qaResult.issues?.length || 0})</h3>
                                    {(!qaResult.issues || qaResult.issues.length === 0) ? (
                                        <p className="text-xs text-gray-500 italic">無發現任何待改進的問題。</p>
                                    ) : (
                                        <div className="grid gap-3 sm:grid-cols-1">
                                            {qaResult.issues.map((issue: any, index: number) => {
                                                // Check Type styling
                                                let typeName = '定位契合';
                                                let typeColor = 'bg-blue-50 text-blue-700 border-blue-100';
                                                if (issue.check_type === 'restricted') {
                                                    typeName = '禁用邊界';
                                                    typeColor = 'bg-amber-50 text-amber-700 border-amber-100';
                                                } else if (issue.check_type === 'info_gain') {
                                                    typeName = '資訊增益';
                                                    typeColor = 'bg-indigo-50 text-indigo-700 border-indigo-100';
                                                } else if (issue.check_type === 'cta') {
                                                    typeName = 'CTA 導向';
                                                    typeColor = 'bg-purple-50 text-purple-700 border-purple-100';
                                                }

                                                return (
                                                    <div key={index} className="p-4 rounded-lg border border-gray-100 bg-gray-50/50 hover:bg-gray-50 transition-colors flex flex-col gap-2.5">
                                                        <div className="flex items-center justify-between gap-2">
                                                            <div className="flex items-center gap-2">
                                                                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${typeColor}`}>
                                                                    {typeName}
                                                                </span>
                                                                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                                                                    issue.severity === 'error'
                                                                        ? 'bg-rose-50 text-rose-700 border-rose-100'
                                                                        : 'bg-yellow-50 text-yellow-700 border-yellow-100'
                                                                }`}>
                                                                    {issue.severity === 'error' ? '必修項目' : '建議優化'}
                                                                </span>
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <p className="text-sm font-medium text-gray-800">{issue.description}</p>
                                                            <p className="text-xs text-gray-600 mt-1.5 bg-white p-2.5 rounded border border-gray-100 leading-relaxed">
                                                                <span className="font-semibold text-indigo-600">優化建議：</span>
                                                                {issue.suggestion}
                                                            </p>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                                
                                {qaResult.issues?.length > 0 && (
                                    <div className="text-xs text-gray-500 pt-2 flex items-center justify-between">
                                        <span>建議直接複製下方的文章內容進行手動調整，以快速通過稽核。</span>
                                        <button
                                            onClick={handleRunQA}
                                            className="text-indigo-600 hover:text-indigo-700 font-medium inline-flex items-center gap-1"
                                        >
                                            <RotateCcw className="w-3 h-3" />
                                            重新審查
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Version Control Panel */}
                    {createdDraftId && (
                        <div className="card border border-gray-100 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md shadow-sm p-5 space-y-4">
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                        <RotateCcw className="w-5 h-5 text-indigo-500" />
                                        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">版本控制與歷史還原</h2>
                                    </div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">
                                        系統在重新生成文章前會自動備份舊版本。您也可以手動儲存目前版本。當前版本：V{versions.length > 0 ? Math.max(...versions.map(v => v.version)) : 1}。
                                    </p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={handleSaveVersion}
                                        className="btn-secondary text-sm py-2 px-4 flex items-center gap-1.5"
                                    >
                                        <Plus className="w-4 h-4" />
                                        手動儲存版本
                                    </button>
                                    <button
                                        onClick={() => setShowVersionsModal(true)}
                                        className="btn-secondary text-sm py-2 px-4 flex items-center gap-1.5"
                                    >
                                        <BookOpen className="w-4 h-4" />
                                        查看版本歷史 ({versions.length})
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

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

            {/* Versions Modal */}
            {showVersionsModal && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-gray-100 dark:border-slate-800 space-y-6">
                        <div className="flex items-center justify-between border-b border-gray-100 dark:border-slate-800 pb-4">
                            <div className="flex items-center gap-2">
                                <RotateCcw className="w-5 h-5 text-indigo-500" />
                                <h3 className="text-lg font-bold text-gray-950 dark:text-gray-50">版本歷史紀錄</h3>
                            </div>
                            <button
                                onClick={() => setShowVersionsModal(false)}
                                className="p-1.5 hover:bg-gray-100 dark:hover:bg-slate-850 rounded-lg text-gray-500"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="max-h-96 overflow-y-auto space-y-3 pr-2">
                            {loadingVersions ? (
                                <div className="py-8 flex justify-center">
                                    <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                                </div>
                            ) : versions.length === 0 ? (
                                <p className="text-center py-8 text-sm text-gray-500 italic">尚未有任何歷史備份版本。</p>
                            ) : (
                                [...versions].sort((a, b) => b.version - a.version).map((v) => (
                                    <div
                                        key={v.id}
                                        className="p-4 border border-gray-100 dark:border-slate-800 rounded-xl bg-gray-50/50 dark:bg-slate-900/50 flex items-center justify-between gap-4 hover:border-indigo-100 transition-colors"
                                    >
                                        <div className="space-y-1">
                                            <div className="flex items-center gap-2">
                                                <span className="font-bold text-indigo-600 text-sm">
                                                    版本 V{v.version}
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    {new Date(v.created_at).toLocaleString('zh-TW')}
                                                </span>
                                            </div>
                                            <p className="text-xs text-gray-700 dark:text-gray-300 truncate max-w-md">
                                                標題：{v.title || '（無標題）'}
                                            </p>
                                            <div className="text-[10px] text-gray-500 flex items-center gap-3">
                                                <span>字數：{v.word_count?.toLocaleString() || 0} 字</span>
                                                <span>狀態：{v.status === 'draft' ? '草稿' : v.status}</span>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => handleRollback(v.id)}
                                            className="btn-secondary text-xs py-1.5 px-3 border border-indigo-200 text-indigo-600 hover:bg-indigo-50"
                                        >
                                            還原此版本
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>

                        <div className="flex justify-end border-t border-gray-100 dark:border-slate-800 pt-4">
                            <button
                                onClick={() => setShowVersionsModal(false)}
                                className="btn-secondary px-5"
                            >
                                關閉
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default ContentGeneration
