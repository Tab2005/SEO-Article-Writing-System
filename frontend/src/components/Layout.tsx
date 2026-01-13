import { Outlet, Link, useLocation } from 'react-router-dom'
import { Sparkles, LayoutDashboard, Search, FileText, FolderOpen, Target, Settings, LogOut, Wand2 } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { authService } from '../services/auth.service'
import { ThemeToggle } from './ThemeToggle'

function Layout() {
    const location = useLocation()
    const { user, clearAuth } = useAuthStore()

    const handleLogout = async () => {
        try {
            await authService.logout()
        } catch {
            clearAuth()
        }
    }

    const navItems = [
        { path: '/', icon: LayoutDashboard, label: '儀表板' },
        { path: '/research', icon: Search, label: '關鍵字研究' },
        { path: '/content', icon: FileText, label: '內容生成' },
        { path: '/strategy-wizard', icon: Wand2, label: '策略導引' },
        { path: '/seo-checker', icon: Target, label: 'SEO 檢查' },
        { path: '/projects', icon: FolderOpen, label: '專案管理' },
        { path: '/settings', icon: Settings, label: '系統設定' },
    ]

    return (
        <div className="min-h-screen page-bg flex">
            {/* Sidebar */}
            <aside className="w-64 sidebar flex flex-col">
                {/* Logo */}
                <div className="h-16 flex items-center justify-between px-6 border-b border-gray-200 dark:border-slate-700">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <span className="font-semibold text-gray-900 dark:text-gray-100">SEO 撰寫系統</span>
                    </div>
                    <ThemeToggle />
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4 space-y-1">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`nav-item ${isActive ? 'nav-item-active' : 'nav-item-inactive'}`}
                            >
                                <item.icon className="w-5 h-5" />
                                <span className="font-medium">{item.label}</span>
                            </Link>
                        )
                    })}
                </nav>

                {/* User section */}
                <div className="p-4 border-t border-gray-200 dark:border-slate-700">
                    <div className="flex items-center gap-3 px-4 py-3 bg-gray-50 dark:bg-slate-800 rounded-lg">
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
