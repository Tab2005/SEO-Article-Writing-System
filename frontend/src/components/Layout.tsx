import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { 
    Sparkles, LayoutDashboard, Search, FileText, FolderOpen, 
    Target, Settings, LogOut, Wand2, ShieldCheck, Compass, GitFork, Cpu, Lock, ChevronRight, ClipboardList
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useProjectStore } from '../store/projectStore'
import { authService } from '../services/auth.service'
import { ThemeToggle } from './ThemeToggle'

function Layout() {
    const location = useLocation()
    const navigate = useNavigate()
    const { user, clearAuth } = useAuthStore()
    const { currentProject } = useProjectStore()

    const handleLogout = async () => {
        try {
            await authService.logout()
        } catch {
            clearAuth()
        }
    }

    const handleItemClick = (e: React.MouseEvent, _path: string, requiresProject: boolean) => {
        if (requiresProject && !currentProject) {
            e.preventDefault()
            alert('請先在「專案管理」中選定或建立一個專案以使用此功能！')
            navigate('/projects')
        }
    }

    const generalItems = [
        { path: '/', icon: LayoutDashboard, label: '儀表板', requiresProject: false },
        { path: '/projects', icon: FolderOpen, label: '專案管理', requiresProject: false },
    ]

    const planningItems = [
        { path: '/project-setup', icon: Compass, label: '專案啟用中心', requiresProject: true },
        { path: '/site-profile', icon: ShieldCheck, label: '網站身份定位', requiresProject: true },
        { path: '/topic-map', icon: GitFork, label: '主題地圖管理', requiresProject: true },
        { path: '/qualification', icon: Cpu, label: '題目評估控制台', requiresProject: true },
        { path: '/briefs', icon: FileText, label: '文章任務書', requiresProject: true },
        { path: '/queue', icon: ClipboardList, label: '內容工作佇列', requiresProject: true },
    ]

    const executionItems = [
        { path: '/research', icon: Search, label: '關鍵字研究', requiresProject: false },
        { path: '/content', icon: FileText, label: '內容生成', requiresProject: false },
        { path: '/strategy-wizard', icon: Wand2, label: '策略導引', requiresProject: false },
        { path: '/seo-checker', icon: Target, label: 'SEO 檢查', requiresProject: false },
        { path: '/settings', icon: Settings, label: '系統設定', requiresProject: false },
    ]

    return (
        <div className="min-h-screen page-bg flex">
            {/* Sidebar */}
            <aside className="w-64 sidebar flex flex-col border-r border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                {/* Logo */}
                <div className="h-16 flex items-center justify-between px-6 border-b border-gray-200 dark:border-slate-800 shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <span className="font-semibold text-gray-900 dark:text-gray-100">SEO 撰寫系統</span>
                    </div>
                    <ThemeToggle />
                </div>

                {/* Current Project Info */}
                {currentProject ? (
                    <div className="px-6 py-3 bg-primary-50/50 dark:bg-primary-950/20 border-b border-gray-100 dark:border-slate-800 flex items-center justify-between gap-2 shrink-0">
                        <div className="min-w-0">
                            <span className="text-[10px] text-gray-400 block font-medium uppercase tracking-wider">目前操作專案</span>
                            <span className="text-xs font-bold text-primary-700 dark:text-primary-400 truncate block mt-0.5">
                                {currentProject.name}
                            </span>
                        </div>
                        <button
                            onClick={() => navigate('/projects')}
                            className="text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 shrink-0"
                            title="切換專案"
                        >
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                ) : (
                    <div className="px-6 py-3 bg-gray-50 dark:bg-slate-800/30 border-b border-gray-100 dark:border-slate-800 flex items-center justify-between gap-2 shrink-0">
                        <div className="min-w-0">
                            <span className="text-[10px] text-gray-400 block font-medium uppercase tracking-wider">目前操作專案</span>
                            <span className="text-xs font-bold text-gray-500 truncate block mt-0.5 italic">
                                未選定專案
                            </span>
                        </div>
                        <button
                            onClick={() => navigate('/projects')}
                            className="text-xs text-primary-600 dark:text-primary-400 font-semibold shrink-0"
                        >
                            去選擇
                        </button>
                    </div>
                )}

                {/* Navigation */}
                <nav className="flex-1 p-4 space-y-6 overflow-y-auto">
                    {/* General Section */}
                    <div className="space-y-1">
                        <span className="text-[10px] text-gray-400 font-bold px-4 uppercase tracking-wider">一般功能</span>
                        {generalItems.map((item) => {
                            const isActive = location.pathname === item.path
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    onClick={(e) => handleItemClick(e, item.path, item.requiresProject)}
                                    className={`nav-item ${isActive ? 'nav-item-active' : 'nav-item-inactive'}`}
                                >
                                    <item.icon className="w-5 h-5" />
                                    <span className="font-medium text-sm">{item.label}</span>
                                </Link>
                            )
                        })}
                    </div>

                    {/* Planning Layer Section */}
                    <div className="space-y-1">
                        <span className="text-[10px] text-gray-400 font-bold px-4 uppercase tracking-wider">上游規劃層</span>
                        {planningItems.map((item) => {
                            const isActive = location.pathname === item.path
                            const isLocked = !currentProject
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    onClick={(e) => handleItemClick(e, item.path, item.requiresProject)}
                                    className={`nav-item ${
                                        isActive 
                                            ? 'nav-item-active' 
                                            : isLocked 
                                            ? 'text-gray-400 dark:text-slate-600 cursor-not-allowed hover:bg-transparent' 
                                            : 'nav-item-inactive'
                                    }`}
                                >
                                    {isLocked ? <Lock className="w-4 h-4 text-gray-400 dark:text-slate-600" /> : <item.icon className="w-5 h-5" />}
                                    <span className="font-medium text-sm">{item.label}</span>
                                </Link>
                            )
                        })}
                    </div>

                    {/* Execution Section */}
                    <div className="space-y-1">
                        <span className="text-[10px] text-gray-400 font-bold px-4 uppercase tracking-wider">執行層與設定</span>
                        {executionItems.map((item) => {
                            const isActive = location.pathname === item.path
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    onClick={(e) => handleItemClick(e, item.path, item.requiresProject)}
                                    className={`nav-item ${isActive ? 'nav-item-active' : 'nav-item-inactive'}`}
                                >
                                    <item.icon className="w-5 h-5" />
                                    <span className="font-medium text-sm">{item.label}</span>
                                </Link>
                            )
                        })}
                    </div>
                </nav>

                {/* User section */}
                <div className="p-4 border-t border-gray-200 dark:border-slate-800 shrink-0">
                    <div className="flex items-center gap-3 px-4 py-3 bg-gray-50 dark:bg-slate-850 rounded-lg">
                        <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900/50 rounded-full flex items-center justify-center">
                            <span className="text-primary-700 dark:text-primary-400 font-medium text-sm">
                                {user?.full_name?.[0] || user?.email?.[0]?.toUpperCase() || 'U'}
                            </span>
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                {user?.full_name || 'User'}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{user?.email}</p>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 
                         hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                            title="登出"
                        >
                            <LogOut className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main content */}
            <main className="flex-1 p-8 overflow-auto">
                <Outlet />
            </main>
        </div>
    )
}

export default Layout
