import { useState } from 'react'
import { FolderOpen, Plus, Search, MoreVertical, FileText, Calendar, Trash2 } from 'lucide-react'

interface Project {
    id: string
    name: string
    description?: string
    articleCount: number
    createdAt: string
    updatedAt: string
}

function Projects() {
    const [searchQuery, setSearchQuery] = useState('')
    const [showNewProjectModal, setShowNewProjectModal] = useState(false)
    const [projects] = useState<Project[]>([])  // Will be populated from API

    const filteredProjects = projects.filter(p =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">專案管理</h1>
                    <p className="text-gray-600 mt-1">管理你的 SEO 文章專案</p>
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
                    placeholder="搜尋專案..."
                    className="input pl-12"
                />
            </div>

            {/* Project List */}
            {filteredProjects.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredProjects.map((project) => (
                        <div
                            key={project.id}
                            className="card hover:shadow-lg transition-shadow cursor-pointer group"
                        >
                            <div className="flex items-start justify-between">
                                <div className="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center">
                                    <FolderOpen className="w-6 h-6 text-primary-600" />
                                </div>
                                <button className="p-2 text-gray-400 hover:text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <MoreVertical className="w-5 h-5" />
                                </button>
                            </div>

                            <h3 className="font-semibold text-gray-900 mt-4">{project.name}</h3>
                            {project.description && (
                                <p className="text-sm text-gray-500 mt-1 line-clamp-2">{project.description}</p>
                            )}

                            <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100 text-sm text-gray-500">
                                <span className="flex items-center gap-1">
                                    <FileText className="w-4 h-4" />
                                    {project.articleCount} 篇文章
                                </span>
                                <span className="flex items-center gap-1">
                                    <Calendar className="w-4 h-4" />
                                    {new Date(project.updatedAt).toLocaleDateString('zh-TW')}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="card flex flex-col items-center justify-center py-16 text-center">
                    <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-6">
                        <FolderOpen className="w-10 h-10 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {searchQuery ? '找不到符合的專案' : '尚無專案'}
                    </h3>
                    <p className="text-gray-500 max-w-md mb-6">
                        {searchQuery
                            ? '請嘗試其他搜尋條件'
                            : '建立你的第一個專案來開始管理 SEO 文章'}
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

            {/* New Project Modal (Placeholder) */}
            {showNewProjectModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">新增專案</h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    專案名稱 *
                                </label>
                                <input type="text" className="input" placeholder="例如：2024 SEO 策略" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    描述
                                </label>
                                <textarea className="input" rows={3} placeholder="專案描述..." />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    目標市場
                                </label>
                                <select className="input">
                                    <option value="tw">台灣</option>
                                    <option value="hk">香港</option>
                                    <option value="us">美國</option>
                                </select>
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 mt-6">
                            <button
                                onClick={() => setShowNewProjectModal(false)}
                                className="btn-secondary"
                            >
                                取消
                            </button>
                            <button className="btn-primary">
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
