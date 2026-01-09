import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, Search, FileText, TrendingUp, AlertTriangle } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

// Check if Google Client ID is configured
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

function Login() {
    const navigate = useNavigate()
    const { setAuth, isLoading, setLoading } = useAuthStore()
    const [error, setError] = useState<string | null>(null)

    // Development mode: bypass login
    const handleDevLogin = () => {
        setLoading(true)
        setError(null)

        // Simulate login with mock user
        setTimeout(() => {
            setAuth(
                'dev-access-token',
                'dev-refresh-token',
                {
                    id: 'dev-user-id',
                    email: 'dev@example.com',
                    full_name: '開發者',
                    is_verified: true,
                }
            )
            navigate('/', { replace: true })
        }, 500)
    }

    // Production: Google OAuth login
    const handleGoogleLogin = async () => {
        if (!GOOGLE_CLIENT_ID) {
            setError('Google OAuth 未設定，請在 .env.local 中設定 VITE_GOOGLE_CLIENT_ID')
            return
        }

        // This would normally use useGoogleLogin hook
        // For now, show configuration message
        setError('請設定 Google OAuth Client ID')
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-100 flex">
            {/* Left side - Branding */}
            <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600 to-primary-800 p-12 flex-col justify-between">
                <div>
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                            <Sparkles className="w-6 h-6 text-white" />
                        </div>
                        <span className="text-white text-xl font-semibold">SEO 文章撰寫系統</span>
                    </div>
                </div>

                <div className="space-y-8">
                    <h1 className="text-4xl font-bold text-white leading-tight">
                        AI 驅動的
                        <br />
                        SEO 內容生成平台
                    </h1>

                    <div className="space-y-4">
                        <div className="flex items-center gap-4 text-white/90">
                            <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center">
                                <Search className="w-5 h-5" />
                            </div>
                            <span>關鍵字研究與競品分析</span>
                        </div>

                        <div className="flex items-center gap-4 text-white/90">
                            <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center">
                                <FileText className="w-5 h-5" />
                            </div>
                            <span>AI 輔助內容生成</span>
                        </div>

                        <div className="flex items-center gap-4 text-white/90">
                            <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center">
                                <TrendingUp className="w-5 h-5" />
                            </div>
                            <span>SEO 優化建議</span>
                        </div>
                    </div>
                </div>

                <div className="text-white/60 text-sm">
                    © 2026 SEO Article Writing System
                </div>
            </div>

            {/* Right side - Login */}
            <div className="flex-1 flex items-center justify-center p-8">
                <div className="w-full max-w-md">
                    {/* Mobile logo */}
                    <div className="lg:hidden flex items-center gap-3 mb-8 justify-center">
                        <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
                            <Sparkles className="w-6 h-6 text-white" />
                        </div>
                        <span className="text-primary-900 text-xl font-semibold">SEO 文章撰寫系統</span>
                    </div>

                    <div className="card">
                        <div className="text-center mb-8">
                            <h2 className="text-2xl font-bold text-gray-900 mb-2">歡迎使用</h2>
                            <p className="text-gray-600">
                                登入以開始使用 SEO 文章撰寫系統
                            </p>
                        </div>

                        {/* Development Mode Notice */}
                        {!GOOGLE_CLIENT_ID && (
                            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                                <div className="flex items-start gap-3">
                                    <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                                    <div>
                                        <p className="font-medium text-yellow-800">開發模式</p>
                                        <p className="text-yellow-700 text-sm mt-1">
                                            Google OAuth 未設定，使用開發者登入
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {error && (
                            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                                {error}
                            </div>
                        )}

                        {/* Dev Login Button */}
                        <button
                            onClick={handleDevLogin}
                            disabled={isLoading}
                            className="w-full mb-4 px-6 py-3 bg-primary-600 text-white font-medium rounded-lg
                       hover:bg-primary-700 focus:outline-none focus:ring-2 
                       focus:ring-primary-500 focus:ring-offset-2
                       transition-all duration-200 ease-in-out
                       disabled:opacity-50 disabled:cursor-not-allowed
                       flex items-center justify-center gap-2"
                        >
                            {isLoading ? (
                                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            ) : (
                                <Sparkles className="w-5 h-5" />
                            )}
                            <span>{isLoading ? '登入中...' : '開發者快速登入'}</span>
                        </button>

                        {/* Google Login Button (when configured) */}
                        {GOOGLE_CLIENT_ID && (
                            <button
                                onClick={handleGoogleLogin}
                                disabled={isLoading}
                                className="google-btn disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <svg className="w-5 h-5" viewBox="0 0 24 24">
                                    <path
                                        fill="#4285F4"
                                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                    />
                                    <path
                                        fill="#34A853"
                                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                    />
                                    <path
                                        fill="#FBBC05"
                                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                    />
                                    <path
                                        fill="#EA4335"
                                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                    />
                                </svg>
                                <span>使用 Google 帳號登入</span>
                            </button>
                        )}

                        <p className="mt-6 text-center text-sm text-gray-500">
                            登入即表示您同意我們的服務條款與隱私政策
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Login
