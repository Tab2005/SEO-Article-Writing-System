import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
    Cpu, CheckCircle, AlertTriangle, XCircle, Search, 
    History, Bookmark, ArrowRight, ShieldAlert, Edit, Save 
} from 'lucide-react'
import { planningService, QualificationResult, TopicNode } from '../services/planning.service'
import { useProjectStore } from '../store/projectStore'

function QualificationPage() {
    const navigate = useNavigate()
    const { currentProject } = useProjectStore()
    const [termInput, setTermInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [history, setHistory] = useState<QualificationResult[]>([])
    const [currentResult, setCurrentResult] = useState<QualificationResult | null>(null)
    const [flatNodes, setFlatNodes] = useState<TopicNode[]>([])

    // Edit result states
    const [isEditing, setIsEditing] = useState(false)
    const [editedStatus, setEditedStatus] = useState<'generated' | 'approved' | 'rejected' | 'edited'>('generated')
    const [editedAngle, setEditedAngle] = useState('')
    const [editedStage, setEditedStage] = useState('')
    const [editedTopicId, setEditedTopicId] = useState('')

    useEffect(() => {
        if (!currentProject) return
        loadHistoryAndNodes()
    }, [currentProject])

    const loadHistoryAndNodes = async () => {
        try {
            const hist = await planningService.getQualificationResults(currentProject!.id)
            setHistory(hist)

            const nodes = await planningService.getTopicNodes(currentProject!.id)
            setFlatNodes(nodes.filter(n => n.status !== 'archived'))
        } catch (err) {
            console.error('Failed to load qualification history:', err)
        }
    }

    const handleEvaluate = async () => {
        if (!termInput.trim() || !currentProject) return
        try {
            setLoading(true)
            const result = await planningService.evaluateTopic(currentProject.id, termInput.trim())
            setCurrentResult(result)
            setTermInput('')
            
            // Reload history to include the new one
            await loadHistoryAndNodes()
            
            // Initialize edit fields
            setEditedStatus(result.review_status)
            setEditedAngle(result.suggested_angle || '')
            setEditedStage(result.target_journey_stage || '')
            setEditedTopicId(result.mapped_topic_id || '')
        } catch (err: any) {
            console.error('Evaluation failed:', err)
            alert(err.response?.data?.detail || '評估失敗，請檢查品牌定位是否已經完備並生成快照。')
        } finally {
            setLoading(false)
        }
    }

    const handleSelectHistory = (res: QualificationResult) => {
        setCurrentResult(res)
        setIsEditing(false)
        setEditedStatus(res.review_status)
        setEditedAngle(res.suggested_angle || '')
        setEditedStage(res.target_journey_stage || '')
        setEditedTopicId(res.mapped_topic_id || '')
    }

    const handleSaveResultEdit = async () => {
        if (!currentProject || !currentResult) return
        try {
            const updated = await planningService.updateQualificationResult(currentProject.id, currentResult.id, {
                review_status: editedStatus === 'generated' ? 'edited' : editedStatus,
                suggested_angle: editedAngle,
                target_journey_stage: editedStage || undefined,
                mapped_topic_id: editedTopicId || undefined
            })
            setCurrentResult(updated)
            setIsEditing(false)
            await loadHistoryAndNodes()
            alert('評估審查結果已成功更新！')
        } catch (err) {
            console.error('Failed to update qualification result:', err)
            alert('更新失敗。')
        }
    }

    const handleCreateBrief = async () => {
        if (!currentProject || !currentResult) return
        try {
            setLoading(true)
            const newBrief = await planningService.createBriefFromQualification(currentProject.id, currentResult.id)
            alert('文章任務書已成功生成！')
            navigate(`/briefs/${newBrief.id}`)
        } catch (err: any) {
            console.error('Failed to generate brief:', err)
            alert(err.response?.data?.detail || '生成任務書失敗，請確認是否已完整配置網站身份定位。')
        } finally {
            setLoading(false)
        }
    }


    const getDecisionBadge = (decision: string) => {
        switch (decision) {
            case 'qualified':
                return (
                    <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-green-50 text-green-700 dark:bg-green-950/30 dark:text-green-400 font-semibold border border-green-200 dark:border-green-900/30">
                        <CheckCircle className="w-3.5 h-3.5" /> 建議採納 (Qualified)
                    </span>
                )
            case 'rewrite_existing':
                return (
                    <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400 font-semibold border border-amber-200 dark:border-amber-900/30">
                        <AlertTriangle className="w-3.5 h-3.5" /> 建議改寫舊文 (Rewrite)
                    </span>
                )
            case 'not_qualified':
                return (
                    <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400 font-semibold border border-red-200 dark:border-red-900/30">
                        <XCircle className="w-3.5 h-3.5" /> 排除題目 (Rejected)
                    </span>
                )
            default:
                return null
        }
    }

    const getFitLevelBadge = (level: string | undefined) => {
        if (!level) return <span className="text-gray-400 font-semibold">-</span>
        switch (level.toLowerCase()) {
            case 'high':
                return <span className="text-xs px-2 py-0.5 rounded bg-green-100 text-green-800 font-semibold dark:bg-green-950 dark:text-green-400">High</span>
            case 'medium':
                return <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-semibold dark:bg-blue-950 dark:text-blue-400">Medium</span>
            case 'low':
                return <span className="text-xs px-2 py-0.5 rounded bg-red-100 text-red-800 font-semibold dark:bg-red-950 dark:text-red-400">Low</span>
            default:
                return <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700 font-semibold">{level}</span>
        }
    }

    const getRiskLevelBadge = (level: string | undefined) => {
        if (!level) return <span className="text-gray-400 font-semibold">None</span>
        switch (level.toLowerCase()) {
            case 'high':
                return <span className="text-xs px-2 py-0.5 rounded bg-red-100 text-red-800 font-semibold dark:bg-red-950 dark:text-red-400">High Risk</span>
            case 'medium':
                return <span className="text-xs px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-semibold dark:bg-amber-950 dark:text-amber-400">Medium Risk</span>
            case 'low':
                return <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-semibold dark:bg-blue-950 dark:text-blue-400">Low Risk</span>
            default:
                return <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-400 font-semibold">None</span>
        }
    }

    if (!currentProject) {
        return (
            <div className="card text-center py-16">
                <Cpu className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">未選定專案</h3>
                <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-6 text-sm">
                    請先至專案管理頁面選擇或建立一個專案，再進行題目適配性評估。
                </p>
                <button onClick={() => navigate('/projects')} className="btn-primary">
                    前往專案管理
                </button>
            </div>
        )
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    題目評估控制台 (Qualification Engine)
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                    輸入一個關鍵字、文章點子或具體題目，系統將啟動品牌定位、防重檢查與 5 維度適配性評估。
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left side: Evaluation trigger and history */}
                <div className="space-y-6 lg:col-span-1">
                    {/* Trigger Card */}
                    <div className="card space-y-4">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm flex items-center gap-2">
                            <Search className="w-4 h-4 text-primary-600" />
                            輸入候選題目
                        </h3>
                        <div className="space-y-3">
                            <input
                                type="text"
                                value={termInput}
                                onChange={(e) => setTermInput(e.target.value)}
                                className="input text-sm"
                                placeholder="例如：2026 電商 SEO 策略"
                                disabled={loading}
                                onKeyDown={(e) => e.key === 'Enter' && handleEvaluate()}
                            />
                            <button
                                onClick={handleEvaluate}
                                disabled={loading || !termInput.trim()}
                                className="btn-primary w-full py-2.5 flex items-center justify-center gap-2 text-sm"
                            >
                                <Cpu className="w-4 h-4 animate-spin-slow" />
                                {loading ? '評估引擎運行中...' : '提交適配性評估'}
                            </button>
                        </div>
                    </div>

                    {/* History Card */}
                    <div className="card flex flex-col h-[400px]">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm pb-3 border-b border-gray-100 dark:border-slate-700 flex items-center gap-2">
                            <History className="w-4 h-4 text-primary-600" />
                            評估歷史紀錄 ({history.length})
                        </h3>
                        <div className="flex-1 overflow-y-auto space-y-1 mt-3 pr-2">
                            {history.length > 0 ? (
                                history.map((res) => {
                                    const isSelected = currentResult?.id === res.id
                                    return (
                                        <div
                                            key={res.id}
                                            onClick={() => handleSelectHistory(res)}
                                            className={`p-3 rounded-lg cursor-pointer transition-colors text-xs flex flex-col gap-1.5 ${
                                                isSelected 
                                                    ? 'bg-primary-50 dark:bg-primary-950/30 border border-primary-200 dark:border-primary-900/30' 
                                                    : 'hover:bg-gray-50 dark:hover:bg-slate-800 border border-transparent'
                                            }`}
                                        >
                                            <div className="flex justify-between items-center gap-2">
                                                <span className="font-bold text-gray-800 dark:text-gray-200 truncate">{res.input_term}</span>
                                                <span className="text-[10px] text-gray-400 shrink-0">
                                                    {new Date(res.created_at).toLocaleDateString('zh-TW')}
                                                </span>
                                            </div>
                                            <div className="flex items-center justify-between text-[10px]">
                                                <span className={`${
                                                    res.decision === 'qualified' ? 'text-green-600' : res.decision === 'rewrite_existing' ? 'text-amber-600' : 'text-red-500'
                                                } font-medium`}>
                                                    {res.decision.toUpperCase()}
                                                </span>
                                                <span className="text-gray-400">
                                                    審查：{res.review_status.toUpperCase()}
                                                </span>
                                            </div>
                                        </div>
                                    )
                                })
                            ) : (
                                <div className="text-center py-16 text-gray-400 text-sm">
                                    尚無評估歷史。請在上方輸入題目提交。
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right side: Detailed Results Panel */}
                <div className="lg:col-span-2 space-y-6">
                    {currentResult ? (
                        <div className="card space-y-6">
                            {/* Summary header */}
                            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4 border-b border-gray-100 dark:border-slate-700 pb-4">
                                <div>
                                    <span className="text-xs text-gray-400">候選關鍵字/題目</span>
                                    <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mt-0.5">
                                        {currentResult.input_term}
                                    </h2>
                                </div>
                                <div className="flex items-center gap-2 shrink-0">
                                    {getDecisionBadge(currentResult.decision)}
                                    {isEditing ? (
                                        <button
                                            onClick={handleSaveResultEdit}
                                            className="text-xs px-2.5 py-1.5 bg-primary-600 text-white rounded hover:bg-primary-700 flex items-center gap-1 font-medium transition-colors"
                                        >
                                            <Save className="w-3.5 h-3.5" /> 儲存
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => setIsEditing(true)}
                                            className="text-xs px-2.5 py-1.5 border border-gray-200 dark:border-slate-600 text-gray-600 dark:text-gray-300 rounded hover:bg-gray-50 dark:hover:bg-slate-700 flex items-center gap-1 font-medium transition-colors"
                                        >
                                            <Edit className="w-3.5 h-3.5" /> 審查決策
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Review Status & Actions Forms */}
                            {isEditing && (
                                <div className="p-4 bg-primary-50/20 dark:bg-primary-950/10 border border-primary-100 dark:border-primary-950/20 rounded-xl space-y-4">
                                    <h4 className="font-semibold text-xs text-gray-800 dark:text-gray-200">手動修改審查決策：</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <div>
                                            <label className="block text-xs text-gray-500 mb-1">審查狀態</label>
                                            <select
                                                value={editedStatus}
                                                onChange={(e) => setEditedStatus(e.target.value as any)}
                                                className="input text-xs py-2 bg-white"
                                            >
                                                <option value="generated">未審核 (Generated)</option>
                                                <option value="approved">通過採納 (Approved)</option>
                                                <option value="rejected">排除捨棄 (Rejected)</option>
                                                <option value="edited">手動修改 (Edited)</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-xs text-gray-500 mb-1">對應主題樹節點</label>
                                            <select
                                                value={editedTopicId}
                                                onChange={(e) => setEditedTopicId(e.target.value)}
                                                className="input text-xs py-2 bg-white"
                                            >
                                                <option value="">[無匹配 - 暫不歸類]</option>
                                                {flatNodes.map(n => (
                                                    <option key={n.id} value={n.id}>{n.name} ({n.topic_role.toUpperCase()})</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-xs text-gray-500 mb-1">建議漏斗階段</label>
                                            <select
                                                value={editedStage}
                                                onChange={(e) => setEditedStage(e.target.value)}
                                                className="input text-xs py-2 bg-white"
                                            >
                                                <option value="">-- 保持原設定 --</option>
                                                <option value="awareness">Awareness</option>
                                                <option value="consideration">Consideration</option>
                                                <option value="decision">Decision</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-xs text-gray-500 mb-1">修改寫作切角建議</label>
                                        <textarea
                                            value={editedAngle}
                                            onChange={(e) => setEditedAngle(e.target.value)}
                                            className="input text-xs bg-white"
                                            rows={2}
                                        />
                                    </div>
                                    <div className="flex justify-end gap-2 text-xs">
                                        <button onClick={() => setIsEditing(false)} className="btn-secondary px-3 py-1.5">取消</button>
                                        <button onClick={handleSaveResultEdit} className="btn-primary px-3 py-1.5">儲存審查結果</button>
                                    </div>
                                </div>
                            )}

                            {/* Summary Reason Box */}
                            <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-lg space-y-2">
                                <h4 className="font-semibold text-gray-700 dark:text-gray-300 text-xs">評估決策說明</h4>
                                <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                                    {currentResult.summary_reason}
                                </p>
                            </div>

                            {/* 5 Fit Dimensions and 2 Risk Dimensions */}
                            {currentResult.decision !== 'not_qualified' && (
                                <div className="space-y-4">
                                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm border-b border-gray-100 dark:border-slate-700 pb-2">
                                        適配度與風險維度分析 (5 Fits & 2 Risks)
                                    </h3>
                                    
                                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                        <div className="border border-gray-100 dark:border-slate-700 p-3 rounded-lg text-center">
                                            <span className="block text-[10px] text-gray-400">品牌定位 (Identity)</span>
                                            <span className="block mt-1">{getFitLevelBadge(currentResult.identity_fit)}</span>
                                        </div>
                                        <div className="border border-gray-100 dark:border-slate-700 p-3 rounded-lg text-center">
                                            <span className="block text-[10px] text-gray-400">核心主題 (Topic)</span>
                                            <span className="block mt-1">{getFitLevelBadge(currentResult.topic_fit)}</span>
                                        </div>
                                        <div className="border border-gray-100 dark:border-slate-700 p-3 rounded-lg text-center">
                                            <span className="block text-[10px] text-gray-400">目標受眾 (Audience)</span>
                                            <span className="block mt-1">{getFitLevelBadge(currentResult.audience_fit)}</span>
                                        </div>
                                        <div className="border border-gray-100 dark:border-slate-700 p-3 rounded-lg text-center">
                                            <span className="block text-[10px] text-gray-400">權威度 (Authority)</span>
                                            <span className="block mt-1">{getFitLevelBadge(currentResult.authority_fit)}</span>
                                        </div>
                                        <div className="border border-gray-100 dark:border-slate-700 p-3 rounded-lg text-center">
                                            <span className="block text-[10px] text-gray-400">業務價值 (Business)</span>
                                            <span className="block mt-1">{getFitLevelBadge(currentResult.business_fit)}</span>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="p-3 bg-gray-50 dark:bg-slate-800 rounded-lg flex items-center justify-between">
                                            <span className="text-xs font-semibold text-gray-600 dark:text-gray-400">舊文重複度風險 (Overlap Risk)</span>
                                            {getRiskLevelBadge(currentResult.overlap_risk)}
                                        </div>
                                        <div className="p-3 bg-gray-50 dark:bg-slate-800 rounded-lg flex items-center justify-between">
                                            <span className="text-xs font-semibold text-gray-600 dark:text-gray-400">品牌邊界偏離風險 (Boundary Risk)</span>
                                            {getRiskLevelBadge(currentResult.boundary_risk)}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Suggested angle and mapped details */}
                            {currentResult.decision === 'qualified' && (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-xs">推薦寫作切角與大綱建議</h4>
                                        <div className="p-3.5 bg-green-50/30 dark:bg-green-950/10 border border-green-100 dark:border-green-950/20 text-xs text-gray-700 dark:text-gray-300 rounded-lg leading-relaxed whitespace-pre-line">
                                            {currentResult.suggested_angle}
                                        </div>
                                    </div>
                                    <div className="space-y-4">
                                        <div>
                                            <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-xs mb-1.5">推薦漏斗階段</h4>
                                            <span className="inline-block text-xs px-2.5 py-1 rounded bg-blue-50 text-blue-700 font-semibold">
                                                {currentResult.target_journey_stage ? currentResult.target_journey_stage.toUpperCase() : '未定義'}
                                            </span>
                                        </div>
                                        <div>
                                            <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-xs mb-1.5">對應的主題地圖節點</h4>
                                            <span className="inline-block text-xs px-2.5 py-1 rounded bg-purple-50 text-purple-700 font-semibold">
                                                {currentResult.mapped_topic_id 
                                                    ? (flatNodes.find(n => n.id === currentResult.mapped_topic_id)?.name || '匹配主題中...')
                                                    : '尚未映射主題節點'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Additional Risks & Alternatives */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {currentResult.risks && currentResult.risks.length > 0 && (
                                    <div className="space-y-2">
                                        <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-xs flex items-center gap-1.5">
                                            <ShieldAlert className="w-3.5 h-3.5 text-red-500" />
                                            辨識出的潛在風險
                                        </h4>
                                        <ul className="list-disc list-inside space-y-1 pl-1">
                                            {currentResult.risks.map((risk, idx) => (
                                                <li key={idx} className="text-xs text-gray-500">{risk}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {currentResult.alternative_topics && currentResult.alternative_topics.length > 0 && (
                                    <div className="space-y-2">
                                        <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-xs flex items-center gap-1.5">
                                            <Bookmark className="w-3.5 h-3.5 text-primary-500" />
                                            替代寫作方向 / 關聯詞
                                        </h4>
                                        <ul className="list-disc list-inside space-y-1 pl-1">
                                            {currentResult.alternative_topics.map((alt, idx) => (
                                                <li key={idx} className="text-xs text-gray-500">{alt}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>

                            {/* Next Step Banner */}
                            {currentResult.recommended_next_step && (
                                <div className="p-4 bg-primary-50/50 dark:bg-primary-950/10 border border-primary-100 dark:border-primary-950/20 rounded-xl flex items-center justify-between text-xs sm:text-sm">
                                    <div className="min-w-0 flex-1">
                                        <span className="font-bold block text-gray-800 dark:text-gray-200">推薦下一步動作：</span>
                                        <span className="text-gray-500 dark:text-gray-400 mt-0.5 block truncate">{currentResult.recommended_next_step}</span>
                                    </div>
                                    {currentResult.decision === 'qualified' && (
                                        <button
                                            onClick={handleCreateBrief}
                                            disabled={loading}
                                            className="ml-4 px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded text-xs font-semibold shrink-0 flex items-center gap-1 transition-colors"
                                        >
                                            {loading ? '處理中...' : '生成任務書 Brief'} <ArrowRight className="w-3.5 h-3.5" />
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="card text-center py-36 text-gray-400">
                            <Cpu className="w-12 h-12 mx-auto text-gray-300 mb-4 animate-pulse" />
                            <p className="text-sm">請在左側輸入一個主題進行適配性評估，或者選擇歷史紀錄查看分析。</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default QualificationPage
