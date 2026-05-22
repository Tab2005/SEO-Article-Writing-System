import { useEffect, useState } from 'react'
import { useProjectStore } from '../store/projectStore'
import { contentService } from '../services/content.service'
import { 
    Kanban, 
    Table, 
    Search, 
    Filter, 
    PlusCircle, 
    FileEdit, 
    BookOpen, 
    Sparkles, 
    CheckCircle2, 
    AlertCircle
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface QueueItem {
    id: string
    keyword: string
    journey_stage: string | null
    topic_id: string | null
    topic_name: string | null
    status: 'qualified' | 'brief_draft' | 'brief_approved' | 'draft_writing' | 'qa_failed' | 'qa_passed' | 'completed'
    created_at: string
    updated_at: string
    qualification_id: string | null
    brief_id: string | null
    draft_id: string | null
}

const STAGES = [
    { key: 'qualified', name: '評估通過', color: 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-950/40 dark:border-blue-800/40 dark:text-blue-400' },
    { key: 'brief_draft', name: '任務書草擬', color: 'bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-950/40 dark:border-amber-800/40 dark:text-amber-400' },
    { key: 'brief_approved', name: '任務書核准', color: 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/40 dark:border-emerald-800/40 dark:text-emerald-400' },
    { key: 'draft_writing', name: '草稿撰寫中', color: 'bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-950/40 dark:border-indigo-800/40 dark:text-indigo-400' },
    { key: 'qa_failed', name: 'QA 未通過', color: 'bg-rose-50 border-rose-200 text-rose-700 dark:bg-rose-950/40 dark:border-rose-800/40 dark:text-rose-400' },
    { key: 'qa_passed', name: 'QA 通過', color: 'bg-teal-50 border-teal-200 text-teal-700 dark:bg-teal-950/40 dark:border-teal-800/40 dark:text-teal-400' },
    { key: 'completed', name: '已發布', color: 'bg-gray-100 border-gray-300 text-gray-700 dark:bg-slate-800 dark:border-slate-700 dark:text-gray-300' }
] as const

const STAGE_LABELS: Record<string, string> = {
    awareness: '認知階段 (Awareness)',
    consideration: '考慮階段 (Consideration)',
    decision: '決策階段 (Decision)'
}

export default function ContentQueue() {
    const { currentProjectId } = useProjectStore()
    const navigate = useNavigate()
    const [viewMode, setViewMode] = useState<'kanban' | 'table'>('kanban')
    const [items, setItems] = useState<QueueItem[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [stageFilter, setStageFilter] = useState<string>('all')
    const [journeyFilter, setJourneyFilter] = useState<string>('all')

    useEffect(() => {
        if (currentProjectId) {
            fetchQueue()
        }
    }, [currentProjectId])

    const fetchQueue = async () => {
        try {
            setLoading(true)
            if (!currentProjectId) return
            const data = await contentService.getContentQueue(currentProjectId)
            setItems(data)
        } catch (error) {
            console.error('Failed to load content queue:', error)
        } finally {
            setLoading(false)
        }
    }

    const filteredItems = items.filter(item => {
        const matchesSearch = item.keyword.toLowerCase().includes(searchQuery.toLowerCase()) || 
                             (item.topic_name && item.topic_name.toLowerCase().includes(searchQuery.toLowerCase()))
        const matchesStage = stageFilter === 'all' || item.status === stageFilter
        const matchesJourney = journeyFilter === 'all' || item.journey_stage === journeyFilter
        return matchesSearch && matchesStage && matchesJourney
    })

    const getJourneyBadgeColor = (stage: string | null) => {
        if (!stage) return 'bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-gray-300'
        if (stage === 'awareness') return 'bg-sky-50 border border-sky-200 text-sky-700 dark:bg-sky-950/30 dark:border-sky-800/30 dark:text-sky-400'
        if (stage === 'consideration') return 'bg-purple-50 border border-purple-200 text-purple-700 dark:bg-purple-950/30 dark:border-purple-800/30 dark:text-purple-400'
        return 'bg-pink-50 border border-pink-200 text-pink-700 dark:bg-pink-950/30 dark:border-pink-800/30 dark:text-pink-400'
    }

    const renderCTAButton = (item: QueueItem) => {
        switch (item.status) {
            case 'qualified':
                return (
                    <button 
                        onClick={() => navigate('/qualification')}
                        className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-primary-600 hover:bg-primary-700 dark:bg-primary-600 dark:hover:bg-primary-500 rounded-lg shadow-sm hover:shadow transition-all duration-200"
                    >
                        <PlusCircle size={14} />
                        建立任務書 (Brief)
                    </button>
                )
            case 'brief_draft':
                return (
                    <button 
                        onClick={() => navigate(`/briefs/${item.brief_id}`)}
                        className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 dark:bg-amber-650 dark:hover:bg-amber-550 rounded-lg shadow-sm hover:shadow transition-all duration-200"
                    >
                        <FileEdit size={14} />
                        編輯任務書
                    </button>
                )
            case 'brief_approved':
                return (
                    <button 
                        onClick={() => navigate(`/content?brief_id=${item.brief_id}`)}
                        className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-650 dark:hover:bg-emerald-550 rounded-lg shadow-sm hover:shadow transition-all duration-200 animate-pulse"
                    >
                        <Sparkles size={14} />
                        撰寫 AI 文章
                    </button>
                )
            case 'draft_writing':
                return (
                    <button 
                        onClick={() => navigate(`/content?brief_id=${item.brief_id}`)}
                        className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 dark:text-indigo-300 dark:bg-indigo-950/40 dark:border-indigo-800/50 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 rounded-lg transition-all duration-200"
                    >
                        <BookOpen size={14} />
                        修改/執行 QA
                    </button>
                )
            case 'qa_failed':
                return (
                    <button 
                        onClick={() => navigate(`/content?brief_id=${item.brief_id}`)}
                        className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 dark:bg-rose-650 dark:hover:bg-rose-550 border border-rose-200 dark:border-rose-800 rounded-lg transition-all duration-200"
                    >
                        <AlertCircle size={14} />
                        修改與重新審查
                    </button>
                )
            case 'qa_passed':
                return (
                    <button 
                        onClick={() => navigate(`/content?brief_id=${item.brief_id}`)}
                        className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 dark:bg-teal-650 dark:hover:bg-teal-550 rounded-lg shadow-sm hover:shadow transition-all duration-200"
                    >
                        <CheckCircle2 size={14} />
                        檢視與準備發布
                    </button>
                )
            default:
                return (
                    <div className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-500 bg-gray-50 border border-gray-200 dark:text-gray-400 dark:bg-slate-800 dark:border-slate-700 rounded-lg cursor-not-allowed">
                        <CheckCircle2 size={14} className="text-gray-400 dark:text-gray-500" />
                        任務已完成
                    </div>
                )
        }
    }

    if (!currentProjectId) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] bg-white/50 dark:bg-slate-800/50 border border-dashed border-gray-200 dark:border-slate-700 rounded-2xl p-8 backdrop-blur-sm">
                <AlertCircle className="text-gray-400 dark:text-gray-500 mb-4" size={48} />
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">請選擇或建立專案</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm text-center max-w-sm mb-4">內容佇列需要關聯至特定的專案，請先在頂部導航欄中選擇您的專案。</p>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header section with styling */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 rounded-2xl p-6 shadow-sm">
                <div>
                    <h1 className="text-2xl font-extrabold text-gray-900 dark:text-gray-100 tracking-tight">內容佇列 (Content Queue)</h1>
                    <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">管理與規劃整站的內容創作流，從關鍵字核准到文章發布一目了然。</p>
                </div>
                <div className="flex items-center gap-2 bg-gray-50 dark:bg-slate-900/50 border border-gray-200/80 dark:border-slate-700 rounded-xl p-1 self-start md:self-auto">
                    <button
                        onClick={() => setViewMode('kanban')}
                        className={`flex items-center gap-1.5 px-3.5 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${viewMode === 'kanban' ? 'bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100 shadow-sm border border-gray-200/50 dark:border-slate-750' : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'}`}
                    >
                        <Kanban size={16} />
                        看板視圖
                    </button>
                    <button
                        onClick={() => setViewMode('table')}
                        className={`flex items-center gap-1.5 px-3.5 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${viewMode === 'table' ? 'bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100 shadow-sm border border-gray-200/50 dark:border-slate-750' : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'}`}
                    >
                        <Table size={16} />
                        表格視圖
                    </button>
                </div>
            </div>

            {/* Filters Bar */}
            <div className="flex flex-col lg:flex-row gap-4 bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 rounded-2xl p-5 shadow-sm">
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500" size={18} />
                    <input
                        type="text"
                        placeholder="搜尋關鍵字或主題名稱..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-slate-750 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 bg-white dark:bg-slate-850 text-gray-900 dark:text-gray-100 transition-all"
                    />
                </div>
                <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2">
                        <Filter className="text-gray-400 dark:text-gray-500" size={16} />
                        <span className="text-xs font-semibold text-gray-500 dark:text-gray-450 uppercase tracking-wider">篩選項目:</span>
                    </div>
                    <select
                        value={stageFilter}
                        onChange={(e) => setStageFilter(e.target.value)}
                        className="px-3.5 py-2 border border-gray-200 dark:border-slate-750 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100 cursor-pointer"
                    >
                        <option value="all">所有工作階段</option>
                        {STAGES.map(s => (
                            <option key={s.key} value={s.key}>{s.name}</option>
                        ))}
                    </select>

                    <select
                        value={journeyFilter}
                        onChange={(e) => setJourneyFilter(e.target.value)}
                        className="px-3.5 py-2 border border-gray-200 dark:border-slate-750 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100 cursor-pointer"
                    >
                        <option value="all">所有搜尋意圖階段</option>
                        <option value="awareness">認知階段 (Awareness)</option>
                        <option value="consideration">考慮階段 (Consideration)</option>
                        <option value="decision">決策階段 (Decision)</option>
                    </select>

                    <button 
                        onClick={fetchQueue}
                        className="px-4 py-2 text-sm text-gray-650 dark:text-gray-300 bg-gray-50 dark:bg-slate-700/50 hover:bg-gray-100 dark:hover:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-xl font-medium transition-all"
                    >
                        重新整理
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="flex flex-col items-center justify-center min-h-[300px]">
                    <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-500 border-t-transparent mb-4"></div>
                    <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">載入佇列中，請稍候...</p>
                </div>
            ) : viewMode === 'kanban' ? (
                /* Kanban View */
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 xxl:grid-cols-7 gap-5 overflow-x-auto pb-4">
                    {STAGES.map(column => {
                        const columnItems = filteredItems.filter(item => item.status === column.key)
                        return (
                            <div key={column.key} className="flex flex-col min-w-[270px] bg-slate-50/50 dark:bg-slate-900/40 border border-slate-200/60 dark:border-slate-800/80 rounded-2xl p-4 h-[650px] shadow-inner">
                                <div className="flex items-center justify-between mb-4 pb-2 border-b border-gray-250/50 dark:border-slate-750/50">
                                    <span className={`px-2.5 py-1 text-xs font-bold rounded-lg border ${column.color}`}>
                                        {column.name}
                                    </span>
                                    <span className="text-xs font-bold bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-750 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded-full shadow-sm">
                                        {columnItems.length}
                                    </span>
                                </div>

                                <div className="flex-1 overflow-y-auto space-y-3.5 pr-1">
                                    {columnItems.length === 0 ? (
                                        <div className="flex flex-col items-center justify-center h-48 border-2 border-dashed border-gray-200/60 dark:border-slate-800 rounded-xl p-4 text-center">
                                            <p className="text-gray-400 dark:text-gray-500 text-xs font-medium">暫無項目</p>
                                        </div>
                                    ) : (
                                        columnItems.map(item => (
                                            <div 
                                                key={item.id}
                                                className="group bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 hover:border-primary-500 dark:hover:border-primary-400 hover:shadow-md rounded-xl p-4 space-y-3.5 transition-all duration-200 cursor-pointer"
                                                onClick={() => {
                                                    // Auto navigation logic based on status
                                                    if (item.status === 'qualified') navigate('/qualification')
                                                    else if (item.status === 'brief_draft') navigate(`/briefs/${item.brief_id}`)
                                                    else navigate(`/content?brief_id=${item.brief_id}`)
                                                }}
                                            >
                                                <div className="space-y-1.5">
                                                    {item.topic_name && (
                                                        <span className="inline-block text-[10px] font-bold text-gray-500 dark:text-gray-450 bg-gray-100 dark:bg-slate-700/60 border border-gray-200 dark:border-slate-700 px-2 py-0.5 rounded-md">
                                                            {item.topic_name}
                                                        </span>
                                                    )}
                                                    <h4 className="text-sm font-bold text-gray-800 dark:text-gray-200 leading-snug group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors line-clamp-2">
                                                        {item.keyword}
                                                    </h4>
                                                </div>

                                                <div className="flex flex-wrap items-center gap-1.5">
                                                    {item.journey_stage && (
                                                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border ${getJourneyBadgeColor(item.journey_stage)}`}>
                                                            {item.journey_stage === 'awareness' ? '認知' : item.journey_stage === 'consideration' ? '考慮' : '決策'}
                                                        </span>
                                                    )}
                                                </div>

                                                <div className="text-[10px] text-gray-400 dark:text-gray-500 font-medium">
                                                    更新於 {new Date(item.updated_at).toLocaleString()}
                                                </div>

                                                <div className="pt-2 border-t border-gray-100 dark:border-slate-750" onClick={(e) => e.stopPropagation()}>
                                                    {renderCTAButton(item)}
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        )
                    })}
                </div>
            ) : (
                /* Table View */
                <div className="bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 rounded-2xl shadow-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-gray-100 dark:border-slate-700 bg-gray-50/50 dark:bg-slate-900/30">
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 dark:text-gray-450 uppercase tracking-wider">關鍵字 / 規劃方向</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 dark:text-gray-450 uppercase tracking-wider">歸屬主題</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 dark:text-gray-450 uppercase tracking-wider">搜尋意圖階段</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 dark:text-gray-450 uppercase tracking-wider">當前進度</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 dark:text-gray-450 uppercase tracking-wider">最後更新</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-500 dark:text-gray-450 uppercase tracking-wider text-right">操作</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 dark:divide-slate-750">
                                {filteredItems.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-12 text-center text-gray-500 dark:text-gray-400 text-sm font-medium">
                                            沒有符合篩選條件的佇列項目。
                                        </td>
                                    </tr>
                                ) : (
                                    filteredItems.map(item => {
                                        const column = STAGES.find(s => s.key === item.status)
                                        return (
                                            <tr key={item.id} className="hover:bg-gray-50/40 dark:hover:bg-slate-700/20 transition-colors">
                                                <td className="px-6 py-4">
                                                    <span className="text-sm font-bold text-gray-900 dark:text-gray-100">{item.keyword}</span>
                                                </td>
                                                <td className="px-6 py-4">
                                                    {item.topic_name ? (
                                                        <span className="text-xs font-semibold text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-slate-700/60 border border-gray-200 dark:border-slate-700 px-2 py-1 rounded-lg">
                                                            {item.topic_name}
                                                        </span>
                                                    ) : (
                                                        <span className="text-xs text-gray-400 dark:text-gray-500 font-medium">未綁定</span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4">
                                                    {item.journey_stage ? (
                                                        <span className={`text-xs font-semibold px-2 py-1 rounded-lg border ${getJourneyBadgeColor(item.journey_stage)}`}>
                                                            {STAGE_LABELS[item.journey_stage] || item.journey_stage}
                                                        </span>
                                                    ) : (
                                                        <span className="text-xs text-gray-400 dark:text-gray-500 font-medium">-</span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-2.5 py-1 text-xs font-bold rounded-lg border ${column?.color}`}>
                                                        {column?.name}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-xs text-gray-500 dark:text-gray-400 font-medium">
                                                    {new Date(item.updated_at).toLocaleString()}
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <div className="inline-block" onClick={(e) => e.stopPropagation()}>
                                                        {renderCTAButton(item)}
                                                    </div>
                                                </td>
                                            </tr>
                                        )
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}

