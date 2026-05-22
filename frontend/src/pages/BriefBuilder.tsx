import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
    ArrowLeft, Save, CheckCircle, XCircle, FileText, 
    Link, AlertCircle, Info, HelpCircle
} from 'lucide-react'
import { planningService, TopicNode } from '../services/planning.service'
import { useProjectStore } from '../store/projectStore'

function BriefBuilder() {
    const { briefId } = useParams<{ briefId: string }>()
    const navigate = useNavigate()
    const { currentProject } = useProjectStore()
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [topicNodes, setTopicNodes] = useState<TopicNode[]>([])

    // Form inputs
    const [titleDirection, setTitleDirection] = useState('')
    const [articleRole, setArticleRole] = useState('')
    const [searchIntent, setSearchIntent] = useState('')
    const [targetAudience, setTargetAudience] = useState('')
    const [primaryQuestion, setPrimaryQuestion] = useState('')
    const [nextQuestion, setNextQuestion] = useState('')
    const [infoGainRequirement, setInfoGainRequirement] = useState('')
    const [restrictedContent, setRestrictedContent] = useState('')
    const [recommendedInternalLinks, setRecommendedInternalLinks] = useState('')
    const [ctaDirection, setCtaDirection] = useState('')
    const [status, setStatus] = useState('draft')
    const [mappedTopicId, setMappedTopicId] = useState('')

    useEffect(() => {
        if (!currentProject || !briefId) return
        loadData()
    }, [currentProject, briefId])

    const loadData = async () => {
        try {
            setLoading(true)
            const [briefData, nodeList] = await Promise.all([
                planningService.getBrief(currentProject!.id, briefId!),
                planningService.getTopicNodes(currentProject!.id)
            ])
            
            setTopicNodes(nodeList.filter(n => n.status !== 'archived'))
            
            // Map values to states
            setTitleDirection(briefData.title_direction)
            setArticleRole(briefData.article_role || '')
            setSearchIntent(briefData.search_intent || '')
            setTargetAudience(briefData.target_audience || '')
            setPrimaryQuestion(briefData.primary_question || '')
            setNextQuestion(briefData.next_question || '')
            setInfoGainRequirement(briefData.info_gain_requirement || '')
            setRestrictedContent(briefData.restricted_content || '')
            setRecommendedInternalLinks(briefData.recommended_internal_links || '')
            setCtaDirection(briefData.cta_direction || '')
            setStatus(briefData.status)
            setMappedTopicId(briefData.mapped_topic_id || '')
        } catch (err) {
            console.error('Failed to load brief detail:', err)
            alert('無法載入任務書詳情，請確認該任務書是否存在。')
            navigate('/briefs')
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async (customStatus?: string) => {
        if (!currentProject || !briefId) return
        if (!titleDirection.trim()) {
            alert('請填寫標題方向！')
            return
        }

        try {
            setSaving(true)
            const nextStatus = customStatus || status
            const updated = await planningService.updateBrief(currentProject.id, briefId, {
                title_direction: titleDirection.trim(),
                article_role: articleRole.trim() || undefined,
                search_intent: searchIntent.trim() || undefined,
                target_audience: targetAudience.trim() || undefined,
                primary_question: primaryQuestion.trim() || undefined,
                next_question: nextQuestion.trim() || undefined,
                info_gain_requirement: infoGainRequirement.trim() || undefined,
                restricted_content: restrictedContent.trim() || undefined,
                recommended_internal_links: recommendedInternalLinks.trim() || undefined,
                cta_direction: ctaDirection.trim() || undefined,
                status: nextStatus,
                mapped_topic_id: mappedTopicId || undefined
            })
            
            setStatus(updated.status)
            alert('儲存成功！')
            if (customStatus) {
                navigate('/briefs')
            }
        } catch (err: any) {
            console.error('Failed to save brief:', err)
            alert(err.response?.data?.detail || '儲存失敗。')
        } finally {
            setSaving(false)
        }
    }

    const getStatusLabel = (s: string) => {
        switch (s) {
            case 'approved':
                return <span className="text-green-600 dark:text-green-400 font-semibold">已核准 (Approved)</span>
            case 'rejected':
                return <span className="text-red-600 dark:text-red-400 font-semibold">已退回 (Rejected)</span>
            case 'draft':
            default:
                return <span className="text-blue-600 dark:text-blue-400 font-semibold">草稿 (Draft)</span>
        }
    }

    if (!currentProject) {
        return (
            <div className="card text-center py-16">
                <p className="text-gray-600 dark:text-gray-400">請先選擇專案。</p>
            </div>
        )
    }

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-20">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary-600"></div>
                <p className="mt-4 text-gray-500 dark:text-gray-400">載入文章任務書詳情中...</p>
            </div>
        )
    }

    return (
        <div className="space-y-8 animate-fade-in max-w-5xl mx-auto pb-12">
            {/* Breadcrumb Navigation */}
            <div className="flex items-center justify-between">
                <button
                    onClick={() => navigate('/briefs')}
                    className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" /> 返回文章任務書清單
                </button>
                <div className="flex items-center gap-2 text-sm">
                    <span className="text-gray-500">當前狀態：</span>
                    {getStatusLabel(status)}
                </div>
            </div>

            {/* Main Action Bar */}
            <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-gray-100 dark:border-slate-700/50 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-primary-50 dark:bg-primary-950/40 rounded-xl flex items-center justify-center text-primary-600 dark:text-primary-400 shrink-0">
                        <FileText className="w-6 h-6" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                            {titleDirection || '未命名任務書'}
                        </h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                            編號: <span className="font-mono text-xs">{briefId}</span>
                        </p>
                    </div>
                </div>

                <div className="flex flex-wrap gap-2 w-full md:w-auto justify-end">
                    <button
                        onClick={() => handleSave()}
                        disabled={saving}
                        className="btn btn-outline flex items-center gap-2 text-sm"
                    >
                        <Save className="w-4 h-4" /> 儲存草稿
                    </button>
                    {status !== 'approved' && (
                        <button
                            onClick={() => handleSave('approved')}
                            disabled={saving}
                            className="btn btn-primary flex items-center gap-2 text-sm bg-green-600 hover:bg-green-700 border-green-600 hover:border-green-700 text-white"
                        >
                            <CheckCircle className="w-4 h-4" /> 核准任務書
                        </button>
                    )}
                    {status !== 'rejected' && status !== 'draft' && (
                        <button
                            onClick={() => handleSave('rejected')}
                            disabled={saving}
                            className="btn btn-outline flex items-center gap-2 text-sm text-red-600 hover:bg-red-50 hover:text-red-700 border-red-200 dark:border-red-950 dark:hover:bg-red-950/30"
                        >
                            <XCircle className="w-4 h-4" /> 退回審核
                        </button>
                    )}
                </div>
            </div>

            {/* Layout Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Form Panel: 2 Columns on LG */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Basic Section */}
                    <div className="card space-y-6">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 border-b pb-3 border-gray-100 dark:border-slate-700/60">
                            基本要求 (Core Settings)
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                    標題方向 / 擬定標題 <span className="text-red-500">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={titleDirection}
                                    onChange={(e) => setTitleDirection(e.target.value)}
                                    placeholder="例如：2026 最新台北戶外露營區推薦，免裝備懶人露營全攻略"
                                    className="w-full rounded-lg border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100 focus:ring-primary-500 focus:border-primary-500"
                                />
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                        對應主題節點 (Topic Node)
                                    </label>
                                    <select
                                        value={mappedTopicId}
                                        onChange={(e) => setMappedTopicId(e.target.value)}
                                        className="w-full rounded-lg border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100 focus:ring-primary-500"
                                    >
                                        <option value="">-- 選擇關聯主題 --</option>
                                        {topicNodes.map(node => (
                                            <option key={node.id} value={node.id}>
                                                {node.name} ({node.topic_role})
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                        文章寫作定位 (Article Role)
                                    </label>
                                    <input
                                        type="text"
                                        value={articleRole}
                                        onChange={(e) => setArticleRole(e.target.value)}
                                        placeholder="例如：資訊型 (Informational) 或 比較型"
                                        className="w-full rounded-lg border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100 focus:ring-primary-500"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                    目標讀者 / 受眾 (Target Audience)
                                </label>
                                <textarea
                                    value={targetAudience}
                                    onChange={(e) => setTargetAudience(e.target.value)}
                                    placeholder="描述讀者的特徵、當前的困境、痛點或背景知識..."
                                    rows={2}
                                    className="w-full rounded-lg border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100 focus:ring-primary-500"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Content Logic Section */}
                    <div className="card space-y-6">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 border-b pb-3 border-gray-100 dark:border-slate-700/60">
                            內容脈絡邏輯 (Content Logic)
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">
                                    核心解答問題 (Primary Question)
                                    <span className="text-gray-400 cursor-help" title="文章首要必須解答的關鍵問題"><Info className="w-4 h-4" /></span>
                                </label>
                                <textarea
                                    value={primaryQuestion}
                                    onChange={(e) => setPrimaryQuestion(e.target.value)}
                                    placeholder="讀者搜尋這個詞時，最渴望立刻獲得什麼答案？"
                                    rows={2}
                                    className="w-full rounded-lg border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">
                                    下一步追問問題 (Next Question)
                                    <span className="text-gray-400 cursor-help" title="在得到主要解答後，讀者會順理成章想知道什麼問題？"><Info className="w-4 h-4" /></span>
                                </label>
                                <textarea
                                    value={nextQuestion}
                                    onChange={(e) => setNextQuestion(e.target.value)}
                                    placeholder="得到核心答案後，下一個最可能延伸或追問的步驟是什麼？"
                                    rows={2}
                                    className="w-full rounded-lg border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                    資訊增益要求 (Information Gain Requirement)
                                </label>
                                <textarea
                                    value={infoGainRequirement}
                                    onChange={(e) => setInfoGainRequirement(e.target.value)}
                                    placeholder="指出哪些獨特觀點、實測數據、第一手經驗或切角，是網路上現有文章缺乏，但我們必須提供的？"
                                    rows={3}
                                    className="w-full rounded-lg border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Form Panel: Constraints & SEO Details */}
                <div className="space-y-6">
                    {/* Constraints */}
                    <div className="card space-y-6 bg-slate-50/50 dark:bg-slate-800/40">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 border-b pb-3 border-gray-100 dark:border-slate-700/60">
                            寫作約束與引導
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                    搜尋意圖 (Search Intent)
                                </label>
                                <input
                                    type="text"
                                    value={searchIntent}
                                    onChange={(e) => setSearchIntent(e.target.value)}
                                    placeholder="例如：比較不同方案、尋找解決步驟"
                                    className="w-full rounded-lg border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-red-600 dark:text-red-400 mb-1 flex items-center gap-1">
                                    禁用與邊界內容 (Restricted Content)
                                    <AlertCircle className="w-4 h-4 shrink-0" />
                                </label>
                                <textarea
                                    value={restrictedContent}
                                    onChange={(e) => setRestrictedContent(e.target.value)}
                                    placeholder="嚴格禁止提及的品牌競爭對手、敏感字眼或偏離主題的切角..."
                                    rows={3}
                                    className="w-full rounded-lg border-red-200 dark:border-red-950/50 bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100 focus:ring-red-500 focus:border-red-500 text-sm"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">
                                    內部連結建議 (Recommended Internal Links)
                                    <Link className="w-4 h-4" />
                                </label>
                                <textarea
                                    value={recommendedInternalLinks}
                                    onChange={(e) => setRecommendedInternalLinks(e.target.value)}
                                    placeholder="建議文章中引用的舊文章 URL 或錨點文字（每行一個）..."
                                    rows={2}
                                    className="w-full rounded-lg border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100 text-sm"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                    行動作召導向 (CTA Direction)
                                </label>
                                <textarea
                                    value={ctaDirection}
                                    onChange={(e) => setCtaDirection(e.target.value)}
                                    placeholder="讀者讀完後，我們要引導他們進行什麼下一步？（例如：預約體驗、註冊會員、下載型錄）"
                                    rows={2}
                                    className="w-full rounded-lg border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-900 dark:text-gray-100 text-sm"
                                />
                            </div>
                        </div>
                    </div>

                    {/* AI Info Card */}
                    <div className="p-5 rounded-2xl bg-primary-50/50 dark:bg-primary-950/10 border border-primary-100 dark:border-primary-900/30 space-y-3">
                        <div className="flex items-center gap-2 text-primary-800 dark:text-primary-300 font-semibold text-sm">
                            <HelpCircle className="w-4 h-4" />
                            什麼是文章任務書？
                        </div>
                        <p className="text-xs text-primary-700/80 dark:text-primary-400/80 leading-relaxed">
                            文章任務書是「題目評估 (Qualification)」與「內容生成 (Generation)」之間的品質控制點。
                            在此定義的核心解答問題、資訊增益要求與禁用邊界將在後續寫作時，<strong>自動餵入 AI 生成器的 System Prompt</strong>，
                            強制 AI 避開套路化廢話，寫出真正具備獨特價值、符合轉換目標的高質量文章。
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default BriefBuilder
