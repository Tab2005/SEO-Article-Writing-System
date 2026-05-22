import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
    FileText, Plus, Search, Trash2, Edit2, CheckCircle, 
    Clock, AlertCircle, ArrowRight, BookOpen 
} from 'lucide-react'
import { planningService, ArticleBrief, TopicNode } from '../services/planning.service'
import { useProjectStore } from '../store/projectStore'

function BriefsList() {
    const navigate = useNavigate()
    const { currentProject } = useProjectStore()
    const [briefs, setBriefs] = useState<ArticleBrief[]>([])
    const [topicNodes, setTopicNodes] = useState<TopicNode[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [statusFilter, setStatusFilter] = useState<string>('all')

    useEffect(() => {
        if (!currentProject) return
        loadData()
    }, [currentProject])

    const loadData = async () => {
        try {
            setLoading(true)
            const [briefList, nodeList] = await Promise.all([
                planningService.listBriefs(currentProject!.id),
                planningService.getTopicNodes(currentProject!.id)
            ])
            setBriefs(briefList)
            setTopicNodes(nodeList)
        } catch (err) {
            console.error('Failed to load briefs data:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleDelete = async (briefId: string, e: React.MouseEvent) => {
        e.stopPropagation()
        if (!confirm('確定要刪除這份文章任務書嗎？此操作無法還原。')) return
        try {
            await planningService.deleteBrief(currentProject!.id, briefId)
            setBriefs(prev => prev.filter(b => b.id !== briefId))
        } catch (err) {
            console.error('Failed to delete brief:', err)
            alert('刪除失敗，請稍後再試。')
        }
    }

    const handleCreateManual = async () => {
        try {
            const newBrief = await planningService.createBrief(currentProject!.id, {
                title_direction: '未命名文章任務書',
                status: 'draft'
            })
            navigate(`/briefs/${newBrief.id}`)
        } catch (err) {
            console.error('Failed to create manual brief:', err)
            alert('建立文章任務書失敗。')
        }
    }

    const getTopicName = (topicId?: string) => {
        if (!topicId) return '未關聯主題'
        const node = topicNodes.find(n => n.id === topicId)
        return node ? node.name : '未知主題'
    }

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'approved':
                return (
                    <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-green-50 text-green-700 dark:bg-green-950/30 dark:text-green-400 font-semibold border border-green-200 dark:border-green-900/30">
                        <CheckCircle className="w-3.5 h-3.5" /> 已核准 (Approved)
                    </span>
                )
            case 'rejected':
                return (
                    <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400 font-semibold border border-red-200 dark:border-red-900/30">
                        <AlertCircle className="w-3.5 h-3.5" /> 已退回 (Rejected)
                    </span>
                )
            case 'draft':
            default:
                return (
                    <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400 font-semibold border border-blue-200 dark:border-blue-900/30">
                        <Clock className="w-3.5 h-3.5" /> 草稿 (Draft)
                    </span>
                )
        }
    }

    if (!currentProject) {
        return (
            <div className="card text-center py-16 flex flex-col items-center justify-center">
                <BookOpen className="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4 animate-pulse" />
                <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">未選定專案</h3>
                <p className="text-gray-500 dark:text-gray-400">請先在左上角選擇或前往專案列表建立一個專案。</p>
            </div>
        )
    }

    const filteredBriefs = briefs.filter(brief => {
        const matchesSearch = brief.title_direction.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (brief.target_audience && brief.target_audience.toLowerCase().includes(searchQuery.toLowerCase()))
        
        const matchesStatus = statusFilter === 'all' || brief.status === statusFilter
        return matchesSearch && matchesStatus
    })

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                        <FileText className="w-7 h-7 text-primary-600 dark:text-primary-400" />
                        文章任務書 (Briefs)
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        管理並制定文章的 AI 寫作指引。每一篇 AI 生成文章都必須基於核准的 Brief。
                    </p>
                </div>
                <button
                    onClick={handleCreateManual}
                    className="btn btn-primary flex items-center justify-center gap-2 self-start sm:self-auto"
                >
                    <Plus className="w-4 h-4" />
                    手動建立 Brief
                </button>
            </div>

            {/* Filters & Search */}
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-white dark:bg-slate-800 p-4 rounded-xl border border-gray-100 dark:border-slate-700/50 shadow-sm">
                <div className="relative w-full md:w-80">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="搜尋標題或目標讀者..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-9 w-full rounded-lg border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 focus:ring-primary-500 focus:border-primary-500 text-sm dark:text-gray-100"
                    />
                </div>
                <div className="flex gap-2 w-full md:w-auto">
                    {['all', 'draft', 'approved', 'rejected'].map((status) => (
                        <button
                            key={status}
                            onClick={() => setStatusFilter(status)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize border transition-all ${
                                statusFilter === status
                                    ? 'bg-primary-600 border-primary-600 text-white shadow-sm'
                                    : 'bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700'
                            }`}
                        >
                            {status === 'all' ? '全部' : status === 'draft' ? '草稿' : status === 'approved' ? '已核准' : '已退回'}
                        </button>
                    ))}
                </div>
            </div>

            {/* List Table / Cards */}
            {loading ? (
                <div className="flex flex-col items-center justify-center py-20">
                    <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary-600"></div>
                    <p className="mt-4 text-gray-500 dark:text-gray-400">載入文章任務書中...</p>
                </div>
            ) : filteredBriefs.length === 0 ? (
                <div className="card text-center py-16 flex flex-col items-center justify-center bg-white dark:bg-slate-800 border border-dashed border-gray-200 dark:border-slate-700">
                    <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-3" />
                    <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-1">查無文章任務書</h3>
                    <p className="text-gray-500 dark:text-gray-400 text-sm max-w-md mb-6">
                        目前專案內尚無任務書。您可以手動建立，或是在「題目評估」合格時點擊「生成任務書 Brief」自動導入。
                    </p>
                    <button
                        onClick={handleCreateManual}
                        className="btn btn-outline flex items-center gap-2"
                    >
                        <Plus className="w-4 h-4" /> 立即建立第一個 Brief
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {filteredBriefs.map((brief) => (
                        <div
                            key={brief.id}
                            onClick={() => navigate(`/briefs/${brief.id}`)}
                            className="group relative flex flex-col md:flex-row items-start md:items-center justify-between p-6 bg-white dark:bg-slate-800 rounded-xl border border-gray-100 dark:border-slate-700/60 shadow-sm hover:shadow-md hover:border-primary-500/50 dark:hover:border-primary-500/30 transition-all cursor-pointer"
                        >
                            <div className="space-y-2 flex-1 pr-4">
                                <div className="flex items-center gap-3 flex-wrap">
                                    <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                                        {brief.title_direction}
                                    </h3>
                                    {getStatusBadge(brief.status)}
                                </div>
                                <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 flex-wrap">
                                    <span className="bg-gray-100 dark:bg-slate-700 px-2.5 py-1 rounded">
                                        主題：{getTopicName(brief.mapped_topic_id)}
                                    </span>
                                    {brief.article_role && (
                                        <span className="bg-gray-100 dark:bg-slate-700 px-2.5 py-1 rounded">
                                            定位：{brief.article_role}
                                        </span>
                                    )}
                                    {brief.target_audience && (
                                        <span className="truncate max-w-[250px]" title={brief.target_audience}>
                                            讀者：{brief.target_audience}
                                        </span>
                                    )}
                                    <span>
                                        更新：{new Date(brief.updated_at).toLocaleDateString('zh-TW', {
                                            year: 'numeric',
                                            month: '2-digit',
                                            day: '2-digit',
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        })}
                                    </span>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 mt-4 md:mt-0 self-end md:self-auto">
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        navigate(`/briefs/${brief.id}`)
                                    }}
                                    className="p-2 text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-all"
                                    title="編輯任務書"
                                >
                                    <Edit2 className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={(e) => handleDelete(brief.id, e)}
                                    className="p-2 text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-all"
                                    title="刪除任務書"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                                <ArrowRight className="w-5 h-5 text-gray-300 dark:text-slate-600 group-hover:text-primary-500 dark:group-hover:text-primary-400 transform group-hover:translate-x-1 transition-all" />
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default BriefsList
