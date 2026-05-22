import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle2, AlertCircle, Play, Sparkles, FolderOpen, ArrowRight, Info } from 'lucide-react'
import { planningService, SiteProfile } from '../services/planning.service'
import { useProjectStore } from '../store/projectStore'

function ProjectSetupPage() {
    const navigate = useNavigate()
    const { currentProject, setCurrentProject } = useProjectStore()
    const [profile, setProfile] = useState<SiteProfile | null>(null)
    const [activeNodesCount, setActiveNodesCount] = useState(0)
    const [loading, setLoading] = useState(true)
    const [activating, setActivating] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!currentProject) return
        loadSetupStatus()
    }, [currentProject])

    const loadSetupStatus = async () => {
        try {
            setLoading(true)
            setError(null)
            const projectId = currentProject!.id

            // 1. Get profile
            try {
                const prof = await planningService.getSiteProfile(projectId)
                setProfile(prof)
            } catch (err: any) {
                if (err.response?.status === 404) {
                    setProfile(null)
                } else {
                    throw err;
                }
            }

            // 2. Get active nodes count
            const nodes = await planningService.getTopicNodes(projectId)
            const activeCount = nodes.filter(n => n.status !== 'archived').length
            setActiveNodesCount(activeCount)
        } catch (err) {
            console.error('Failed to load setup status:', err)
            setError('無法讀取專案規劃狀態。')
        } finally {
            setLoading(false)
        }
    }

    const handleActivate = async () => {
        if (!currentProject) return
        try {
            setActivating(true)
            setError(null)
            const updatedProject = await planningService.activateProject(currentProject.id)
            setCurrentProject(updatedProject)
            alert('恭喜！專案已成功啟用！')
            navigate('/qualification')
        } catch (err: any) {
            console.error('Activation failed:', err)
            setError(err.response?.data?.detail || '啟用專案失敗。請確認是否符合啟用條件！')
        } finally {
            setActivating(false)
        }
    }

    if (!currentProject) {
        return (
            <div className="card text-center py-16">
                <FolderOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">未選定專案</h3>
                <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-6 text-sm">
                    請先至專案管理頁面選擇或建立一個專案，再查看專案啟用中心。
                </p>
                <button onClick={() => navigate('/projects')} className="btn-primary">
                    前往專案管理
                </button>
            </div>
        )
    }

    const isProfileReady = profile?.status === 'ready'
    const isTopicMapReady = activeNodesCount > 0
    const isAllReady = isProfileReady && isTopicMapReady
    const isAlreadyActive = currentProject.status === 'active'

    return (
        <div className="space-y-8 max-w-3xl mx-auto">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    專案啟用與規劃中心
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                    當前規劃專案：<span className="font-semibold text-primary-600 dark:text-primary-400">{currentProject.name}</span>
                </p>
            </div>

            {error && (
                <div className="p-4 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/30 text-red-600 dark:text-red-400 rounded-xl text-sm flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 shrink-0" />
                    <span>{error}</span>
                </div>
            )}

            {loading ? (
                <div className="text-center py-12 text-gray-500">載入規劃狀態中...</div>
            ) : isAlreadyActive ? (
                <div className="card border-2 border-green-500 bg-green-50/20 dark:bg-green-950/10 space-y-6 text-center py-10">
                    <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto" />
                    <div className="space-y-2">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">該專案已啟用成功！</h2>
                        <p className="text-sm text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                            您的品牌定位已完成，且主題地圖已開始運行。現在可以前往題目評估控制台，篩選採納新題目，或者到內容生成模組開始寫作文章！
                        </p>
                    </div>
                    <div className="flex justify-center gap-4 pt-2">
                        <button onClick={() => navigate('/qualification')} className="btn-primary text-sm flex items-center gap-1.5">
                            進行題目評估 <ArrowRight className="w-4 h-4" />
                        </button>
                        <button onClick={() => navigate('/content')} className="btn-secondary text-sm">
                            前往內容生成
                        </button>
                    </div>
                </div>
            ) : (
                <div className="space-y-6">
                    {/* Setup Guides Card */}
                    <div className="card space-y-6">
                        <div className="flex items-center gap-2 pb-3 border-b border-gray-100 dark:border-slate-700">
                            <Info className="w-5 h-5 text-primary-600" />
                            <h2 className="font-semibold text-gray-900 dark:text-gray-100">啟用前置檢查清單</h2>
                        </div>

                        <div className="space-y-4">
                            {/* Requirement 1: Site Profile */}
                            <div className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-100 dark:border-slate-700">
                                <div className="mt-0.5">
                                    {isProfileReady ? (
                                        <CheckCircle2 className="w-6 h-6 text-green-500" />
                                    ) : (
                                        <AlertCircle className="w-6 h-6 text-gray-400" />
                                    )}
                                </div>
                                <div className="flex-1">
                                    <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">步驟 1：完備網站身份定位 (Site Profile)</h3>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                        填寫網站名稱、商業類型與描述定位。完備的定位是生成題目切角評估的重要前提。
                                    </p>
                                    {!isProfileReady && (
                                        <button
                                            onClick={() => navigate('/site-profile')}
                                            className="text-xs text-primary-600 hover:text-primary-700 mt-2 font-semibold flex items-center gap-1"
                                        >
                                            前往設定網站定位 <ArrowRight className="w-3 h-3" />
                                        </button>
                                    )}
                                </div>
                                <div className="text-xs font-medium text-gray-400 shrink-0">
                                    {isProfileReady ? '已完備' : '未完備'}
                                </div>
                            </div>

                            {/* Requirement 2: Topic Map Nodes */}
                            <div className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-100 dark:border-slate-700">
                                <div className="mt-0.5">
                                    {isTopicMapReady ? (
                                        <CheckCircle2 className="w-6 h-6 text-green-500" />
                                    ) : (
                                        <AlertCircle className="w-6 h-6 text-gray-400" />
                                    )}
                                </div>
                                <div className="flex-1">
                                    <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">步驟 2：主題地圖包含至少一個主題</h3>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                        在主題地圖中建立至少一個核心 Pillar 或 Supporting 主題。舊站優化模式亦可在此時匯入舊文章。
                                    </p>
                                    <p className="text-xs text-gray-400 mt-0.5">
                                        目前已規劃主題節點數：{activeNodesCount} 個
                                    </p>
                                    {!isTopicMapReady && (
                                        <button
                                            onClick={() => navigate('/topic-map')}
                                            className="text-xs text-primary-600 hover:text-primary-700 mt-2 font-semibold flex items-center gap-1"
                                        >
                                            前往主題地圖規劃 <ArrowRight className="w-3 h-3" />
                                        </button>
                                    )}
                                </div>
                                <div className="text-xs font-medium text-gray-400 shrink-0">
                                    {isTopicMapReady ? '已完成' : '未完成'}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Activation Banner */}
                    <div className="card bg-primary-50/10 dark:bg-primary-950/10 border-2 border-primary-500/20 p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                        <div className="space-y-1">
                            <h3 className="font-bold text-gray-900 dark:text-gray-100 text-lg flex items-center gap-2">
                                <Sparkles className="w-5 h-5 text-primary-600 animate-pulse" />
                                一鍵啟用專案
                            </h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400 max-w-lg">
                                啟用專案後將解鎖題目適配性評估功能，並整合品牌定位進行多維度過濾與 AI 推薦大綱寫作切角。
                            </p>
                        </div>
                        <button
                            onClick={handleActivate}
                            disabled={activating || !isAllReady}
                            className="btn-primary font-semibold flex items-center justify-center gap-2 text-sm whitespace-nowrap self-start md:self-auto disabled:opacity-50"
                        >
                            <Play className="w-4 h-4 fill-white" />
                            {activating ? '正在啟用...' : '正式啟用專案'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}

export default ProjectSetupPage
