import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FolderOpen, Plus, Search, Trash2, Globe } from 'lucide-react'
import { planningService, Project } from '../services/planning.service'
import { useProjectStore } from '../store/projectStore'

function Projects() {
    const navigate = useNavigate()
    const { setCurrentProject, currentProjectId } = useProjectStore()
    const [searchQuery, setSearchQuery] = useState('')
    const [showNewProjectModal, setShowNewProjectModal] = useState(false)
    const [projects, setProjects] = useState<Project[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Form states
    const [name, setName] = useState('')
    const [description, setDescription] = useState('')
    const [targetMarket, setTargetMarket] = useState('tw')
    const [mode, setMode] = useState<'new_site' | 'existing_site'>('new_site')
    const [domain, setDomain] = useState('')

    useEffect(() => {
        loadProjects()
    }, [])

    const loadProjects = async () => {
        try {
            setLoading(true)
            const list = await planningService.listProjects()
            setProjects(list)
            setError(null)
        } catch (err: any) {
            console.error('Failed to load projects:', err)
            setError('無法載入專案列表，請稍後再試。')
        } finally {
            setLoading(false)
        }
    }

    const handleCreateProject = async () => {
        if (!name.trim()) return
        try {
            const newProj = await planningService.createProject({
                name,
                description,
                target_market: targetMarket,
                mode,
                domain: domain.trim() || undefined,
                status: 'draft'
            })
            setShowNewProjectModal(false)
            // Reset form
            setName('')
            setDescription('')
            setTargetMarket('tw')
            setMode('new_site')
            setDomain('')
            
            // Reload list
            loadProjects()
            
            // Automatically select and route to its profile
            setCurrentProject(newProj)
            navigate('/site-profile')
        } catch (err: any) {
            console.error('Failed to create project:', err)
            alert('建立專案失敗，請檢查輸入內容是否完整。')
        }
    }

    const handleDeleteProject = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation()
        if (!confirm('確定要刪除此專案嗎？此操作將會刪除該專案相關的所有規劃與文章數據且無法復原。')) {
            return
        }
        try {
            await planningService.deleteProject(id)
            if (currentProjectId === id) {
                setCurrentProject(null)
            }
            loadProjects()
        } catch (err) {
            console.error('Failed to delete project:', err)
            alert('刪除專案失敗。')
        }
    }

    const handleSelectProject = (project: Project) => {
        setCurrentProject(project)
        // Redirect to site profile
        navigate('/site-profile')
    }

    const filteredProjects = projects.filter(p =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">專案管理</h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        在這裡切換與管理您的 SEO 專案。您可以建立「新站模式」或「舊站優化模式」的專案。
                    </p>
                </div>
                <button
                    onClick={() => setShowNewProjectModal(true)}
                    className="btn-primary flex items-center justify-center gap-2"
                >
                    <Plus className="w-5 h-5" />
                    新增專案
                </button>
            </div>

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="搜尋專案名稱..."
                    className="input pl-12"
                />
            </div>

            {error && (
                <div className="p-4 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-xl">
                    {error}
                </div>
            )}

            {/* Project List */}
            {loading ? (
                <div className="text-center py-12 text-gray-500">載入中...</div>
            ) : filteredProjects.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredProjects.map((project) => {
                        const isCurrent = project.id === currentProjectId
                        return (
                            <div
                                key={project.id}
                                onClick={() => handleSelectProject(project)}
                                className={`card hover:shadow-lg transition-all cursor-pointer group flex flex-col justify-between border-2 ${
                                    isCurrent ? 'border-primary-500 dark:border-primary-400 ring-2 ring-primary-500/20' : 'border-gray-100 dark:border-slate-800'
                                }`}
                            >
                                <div>
                                    <div className="flex items-start justify-between">
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                                            isCurrent ? 'bg-primary-100 dark:bg-primary-900/50' : 'bg-gray-100 dark:bg-slate-700'
                                        }`}>
                                            <FolderOpen className={`w-6 h-6 ${isCurrent ? 'text-primary-600 dark:text-primary-400' : 'text-gray-500'}`} />
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {isCurrent && (
                                                <span className="text-xs px-2 py-1 bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-400 rounded-full font-medium">
                                                    目前專案
                                                </span>
                                            )}
                                            <button
                                                onClick={(e) => handleDeleteProject(project.id, e)}
                                                className="p-2 text-gray-400 hover:text-red-500 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
                                                title="刪除專案"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>

                                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 mt-4 text-lg">
                                        {project.name}
                                    </h3>
                                    {project.description && (
                                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                                            {project.description}
                                        </p>
                                    )}

                                    {/* Project Meta Tags */}
                                    <div className="flex flex-wrap gap-2 mt-3">
                                        <span className={`text-xs px-2 py-0.5 rounded ${
                                            project.mode === 'new_site' 
                                                ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' 
                                                : 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400'
                                        }`}>
                                            {project.mode === 'new_site' ? '新站模式' : '舊站優化'}
                                        </span>
                                        <span className={`text-xs px-2 py-0.5 rounded ${
                                            project.status === 'active' 
                                                ? 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400' 
                                                : 'bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-gray-400'
                                        }`}>
                                            {project.status === 'active' ? '已啟用' : '規劃中 (Draft)'}
                                        </span>
                                    </div>
                                </div>

                                <div className="mt-6 pt-4 border-t border-gray-100 dark:border-slate-700 flex flex-col gap-2 text-sm text-gray-500 dark:text-gray-400">
                                    {project.domain && (
                                        <div className="flex items-center gap-1.5 truncate">
                                            <Globe className="w-4 h-4 text-gray-400" />
                                            <span className="truncate">{project.domain}</span>
                                        </div>
                                    )}
                                    <div className="flex items-center justify-between text-xs text-gray-400">
                                        <span>更新於：{new Date(project.updated_at).toLocaleDateString('zh-TW')}</span>
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                </div>
            ) : (
                <div className="card flex flex-col items-center justify-center py-16 text-center">
                    <div className="w-20 h-20 bg-gray-100 dark:bg-slate-700 rounded-full flex items-center justify-center mb-6">
                        <FolderOpen className="w-10 h-10 text-gray-400 dark:text-gray-500" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                        {searchQuery ? '找不到符合的專案' : '尚無專案'}
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400 max-w-md mb-6 text-sm">
                        {searchQuery
                            ? '請嘗試其他搜尋條件'
                            : '建立一個專案以開始您的品牌網站定位、主題地圖與文章規劃流程。'}
                    </p>
                    {!searchQuery && (
                        <button
                            onClick={() => setShowNewProjectModal(true)}
                            className="btn-primary flex items-center gap-2"
                        >
                            <Plus className="w-5 h-5" />
                            建立專案
                        </button>
                    )}
                </div>
            )}

            {/* New Project Modal */}
            {showNewProjectModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 w-full max-w-lg shadow-xl">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">新增專案</h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    專案名稱 *
                                </label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="input"
                                    placeholder="例如：行銷工具指南部落格"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    專案描述
                                </label>
                                <textarea
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    className="input"
                                    rows={2}
                                    placeholder="簡述此專案的定位或目標..."
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        專案模式 *
                                    </label>
                                    <select
                                        value={mode}
                                        onChange={(e) => setMode(e.target.value as any)}
                                        className="input"
                                    >
                                        <option value="new_site">新站模式 (從零開始規劃)</option>
                                        <option value="existing_site">舊站優化 (匯入現有內容與防重疊)</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        目標市場
                                    </label>
                                    <select
                                        value={targetMarket}
                                        onChange={(e) => setTargetMarket(e.target.value)}
                                        className="input"
                                    >
                                        <option value="tw">台灣 (Traditional Chinese)</option>
                                        <option value="hk">香港 (Traditional Chinese)</option>
                                        <option value="us">美國 (English)</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    網站域名 (Domain)
                                </label>
                                <input
                                    type="text"
                                    value={domain}
                                    onChange={(e) => setDomain(e.target.value)}
                                    className="input"
                                    placeholder="例如：example.com (選填)"
                                />
                                <p className="text-xs text-gray-400 mt-1">
                                    用於舊文庫連結匹配或品牌關鍵字篩選參考。
                                </p>
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 mt-6">
                            <button
                                onClick={() => setShowNewProjectModal(false)}
                                className="btn-secondary"
                            >
                                取消
                            </button>
                            <button
                                onClick={handleCreateProject}
                                disabled={!name.trim()}
                                className="btn-primary"
                            >
                                建立專案
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Projects
