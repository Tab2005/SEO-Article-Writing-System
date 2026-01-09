import { Search, FileText, TrendingUp, Clock } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

function Dashboard() {
    const { user } = useAuthStore()

    const stats = [
        { label: '總研究次數', value: '0', icon: Search, color: 'text-blue-600', bg: 'bg-blue-50' },
        { label: '已生成文章', value: '0', icon: FileText, color: 'text-green-600', bg: 'bg-green-50' },
        { label: 'SEO 改善', value: '0%', icon: TrendingUp, color: 'text-purple-600', bg: 'bg-purple-50' },
    ]

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900">
                    歡迎回來，{user?.full_name || '使用者'}！
                </h1>
                <p className="text-gray-600 mt-1">
                    開始使用 AI 撰寫優質的 SEO 文章
                </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {stats.map((stat, index) => (
                    <div key={index} className="card flex items-center gap-4">
                        <div className={`w-12 h-12 ${stat.bg} rounded-xl flex items-center justify-center`}>
                            <stat.icon className={`w-6 h-6 ${stat.color}`} />
                        </div>
                        <div>
                            <p className="text-sm text-gray-600">{stat.label}</p>
                            <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Quick Actions */}
            <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">快速開始</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <a
                        href="/research"
                        className="flex items-center gap-4 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                        <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center">
                            <Search className="w-5 h-5 text-primary-600" />
                        </div>
                        <div>
                            <p className="font-medium text-gray-900">關鍵字研究</p>
                            <p className="text-sm text-gray-500">分析競爭對手、找出最佳關鍵字</p>
                        </div>
                    </a>

                    <a
                        href="/content"
                        className="flex items-center gap-4 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                        <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
                            <FileText className="w-5 h-5 text-green-600" />
                        </div>
                        <div>
                            <p className="font-medium text-gray-900">AI 內容生成</p>
                            <p className="text-sm text-gray-500">根據關鍵字自動生成優質文章</p>
                        </div>
                    </a>
                </div>
            </div>

            {/* Recent Activity */}
            <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">最近活動</h2>
                <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                    <Clock className="w-12 h-12 text-gray-300 mb-4" />
                    <p>尚無活動記錄</p>
                    <p className="text-sm">開始進行關鍵字研究來查看活動</p>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
