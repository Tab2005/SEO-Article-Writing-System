import { useState, useEffect } from 'react'
import {
    Save, TestTube, CheckCircle2,
    XCircle, Loader2, Eye, EyeOff, Key, Globe, Cpu, Database
} from 'lucide-react'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import { contentService } from '../services/content.service'

interface SettingsData {
    google_api_key: string
    google_cx_id: string
    ai_provider: string
    ai_model: string
    ai_api_key: string
    google_client_id: string
    google_client_secret: string
    has_google_api: boolean
    has_ai_api: boolean
    has_google_oauth: boolean
}

interface TestResult {
    service: string
    success: boolean
    message: string
}

interface AIProvider {
    name: string
    description: string
    requires_sdk: boolean
}

interface AIModel {
    description: string
    provider: string
    max_tokens?: number
}

function Settings() {
    const { isAuthenticated } = useAuthStore()
    const [settings, setSettings] = useState<SettingsData | null>(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)

    // Form fields
    const [googleApiKey, setGoogleApiKey] = useState('')
    const [googleCxId, setGoogleCxId] = useState('')
    const [aiProvider, setAiProvider] = useState('zeabur')
    const [aiModel, setAiModel] = useState('gemini-2.5-flash')
    const [aiApiKey, setAiApiKey] = useState('')
    const [googleClientId, setGoogleClientId] = useState('')
    const [googleClientSecret, setGoogleClientSecret] = useState('')

    // AI Hub related
    const [providers, setProviders] = useState<Record<string, AIProvider>>({})
    const [models, setModels] = useState<Record<string, AIModel>>({})

    // Show/hide toggles
    const [showGoogleKey, setShowGoogleKey] = useState(false)
    const [showAiKey, setShowAiKey] = useState(false)
    const [showOAuthSecret, setShowOAuthSecret] = useState(false)

    // Test results
    const [testingGoogle, setTestingGoogle] = useState(false)
    const [testingAi, setTestingAi] = useState(false)
    const [googleTestResult, setGoogleTestResult] = useState<TestResult | null>(null)
    const [aiTestResult, setAiTestResult] = useState<TestResult | null>(null)

    // Seeding states
    const [seeding, setSeeding] = useState(false)
    const [seedSuccess, setSeedSuccess] = useState<string | null>(null)

    const handleSeedDemo = async () => {
        if (!window.confirm('此操作將會清空所有現有專案、關鍵字、任務書與草稿，並重新預置展示數據。確定要繼續嗎？')) {
            return
        }
        setSeeding(true)
        setError(null)
        setSuccess(null)
        setSeedSuccess(null)
        try {
            await contentService.seedDemo()
            setSeedSuccess('展示專案數據已成功預置！')
            setTimeout(() => {
                window.location.reload()
            }, 1500)
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || '預置數據失敗')
        } finally {
            setSeeding(false)
        }
    }

    // Fetch current settings
    useEffect(() => {
        if (isAuthenticated) {
            fetchSettings()
            fetchProviders()
        } else {
            setLoading(false)
        }
    }, [isAuthenticated])

    // Fetch models when provider changes
    useEffect(() => {
        if (aiProvider && isAuthenticated) {
            fetchModels(aiProvider)
        }
    }, [aiProvider, isAuthenticated])

    const fetchSettings = async () => {
        if (!isAuthenticated) {
            setError('請先登入才能訪問系統設定')
            setLoading(false)
            return
        }

        try {
            const response = await api.get<SettingsData>('/settings')
            setSettings(response.data)
            setAiProvider(response.data.ai_provider || 'zeabur')
            setAiModel(response.data.ai_model || 'gemini-2.5-flash')
        } catch (err: any) {
            if (err.response?.status === 401) {
                setError('登入已過期，請重新登入')
            } else {
                setError('無法載入設定')
            }
        } finally {
            setLoading(false)
        }
    }

    const fetchProviders = async () => {
        try {
            const response = await api.get('/ai/providers')
            setProviders(response.data.providers || {})
        } catch (err) {
            console.error('Failed to fetch AI providers:', err)
        }
    }

    const fetchModels = async (provider: string) => {
        try {
            const response = await api.get(`/ai/models?provider=${provider}`)
            setModels(response.data.models || {})
        } catch (err) {
            console.error('Failed to fetch AI models:', err)
        }
    }


    const handleSaveGoogle = async () => {
        if (!isAuthenticated) {
            setError('請先登入才能儲存設定')
            return
        }

        setSaving(true)
        setError(null)
        setSuccess(null)

        try {
            await api.put('/settings', {
                google_api_key: googleApiKey || undefined,
                google_cx_id: googleCxId || undefined,
            })

            setGoogleApiKey('')
            setGoogleCxId('')
            await fetchSettings()
            setSuccess('Google Search API 設定已儲存！')
        } catch (err: any) {
            setError(err.response?.data?.detail || '儲存失敗')
        } finally {
            setSaving(false)
        }
    }

    const handleSaveAI = async () => {
        if (!isAuthenticated) {
            setError('請先登入才能儲存設定')
            return
        }

        setSaving(true)
        setError(null)
        setSuccess(null)

        try {
            await api.put('/settings', {
                ai_provider: aiProvider,
                ai_model: aiModel,
                ai_api_key: aiApiKey || undefined,
            })

            setAiApiKey('')
            await fetchSettings()
            setSuccess('AI Hub 設定已儲存！')
        } catch (err: any) {
            setError(err.response?.data?.detail || '儲存失敗')
        } finally {
            setSaving(false)
        }
    }

    const handleSaveOAuth = async () => {
        if (!isAuthenticated) {
            setError('請先登入才能儲存設定')
            return
        }

        setSaving(true)
        setError(null)
        setSuccess(null)

        try {
            await api.put('/settings', {
                google_client_id: googleClientId || undefined,
                google_client_secret: googleClientSecret || undefined,
            })

            setGoogleClientId('')
            setGoogleClientSecret('')
            await fetchSettings()
            setSuccess('Google OAuth 設定已儲存！')
        } catch (err: any) {
            setError(err.response?.data?.detail || '儲存失敗')
        } finally {
            setSaving(false)
        }
    }

    const testGoogleSearch = async () => {
        if (!isAuthenticated) {
            setGoogleTestResult({
                service: 'Google Search',
                success: false,
                message: '請先登入',
            })
            return
        }

        setTestingGoogle(true)
        setGoogleTestResult(null)

        try {
            const response = await api.post<TestResult>('/settings/test/google-search')
            setGoogleTestResult(response.data)
        } catch (err: any) {
            setGoogleTestResult({
                service: 'Google Search',
                success: false,
                message: '測試請求失敗',
            })
        } finally {
            setTestingGoogle(false)
        }
    }

    const testAiHub = async () => {
        if (!isAuthenticated) {
            setAiTestResult({
                service: 'AI Hub',
                success: false,
                message: '請先登入',
            })
            return
        }

        setTestingAi(true)
        setAiTestResult(null)

        try {
            const response = await api.post<TestResult>('/settings/test/ai')
            setAiTestResult(response.data)
        } catch (err: any) {
            setAiTestResult({
                service: 'AI Hub',
                success: false,
                message: '測試請求失敗',
            })
        } finally {
            setTestingAi(false)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
            </div>
        )
    }

    // 未登入時顯示提示
    if (!isAuthenticated) {
        return (
            <div className="space-y-8 max-w-4xl">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">系統設定</h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        設定 API 金鑰以啟用搜尋和內容生成功能
                    </p>
                </div>
                <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg text-yellow-700 dark:text-yellow-400">
                    請先登入才能訪問系統設定
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-8 max-w-4xl">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">系統設定</h1>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                    設定 API 金鑰以啟用搜尋和內容生成功能
                </p>
            </div>

            {/* Status Messages */}
            {error && (
                <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400">
                    {error}
                </div>
            )}

            {success && (
                <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-green-700 dark:text-green-400 flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5" />
                    {success}
                </div>
            )}

            {/* Google Custom Search API */}
            <div className="card">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-blue-50 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                        <Globe className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                        <h2 className="font-semibold text-gray-900 dark:text-gray-100">Google Custom Search API</h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400">用於關鍵字研究和競品分析</p>
                    </div>
                    <div className="ml-auto">
                        {settings?.has_google_api ? (
                            <span className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                                <CheckCircle2 className="w-4 h-4" /> 已設定
                            </span>
                        ) : (
                            <span className="flex items-center gap-1 text-gray-400 text-sm">
                                <XCircle className="w-4 h-4" /> 未設定
                            </span>
                        )}
                    </div>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            API Key {settings?.google_api_key && <span className="text-gray-400">({settings.google_api_key})</span>}
                        </label>
                        <div className="relative">
                            <input
                                type={showGoogleKey ? 'text' : 'password'}
                                value={googleApiKey}
                                onChange={(e) => setGoogleApiKey(e.target.value)}
                                placeholder="輸入新的 API Key..."
                                className="input pr-10"
                            />
                            <button
                                type="button"
                                onClick={() => setShowGoogleKey(!showGoogleKey)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                            >
                                {showGoogleKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                            </button>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Custom Search Engine ID (CX) {settings?.google_cx_id && <span className="text-gray-400">({settings.google_cx_id})</span>}
                        </label>
                        <input
                            type="text"
                            value={googleCxId}
                            onChange={(e) => setGoogleCxId(e.target.value)}
                            placeholder="輸入新的 CX ID..."
                            className="input"
                        />
                    </div>

                    <div className="flex items-center gap-3">
                        <button
                            onClick={testGoogleSearch}
                            disabled={testingGoogle}
                            className="btn-secondary flex items-center gap-2 text-sm py-2 disabled:opacity-50"
                        >
                            {testingGoogle ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <TestTube className="w-4 h-4" />
                            )}
                            測試連線
                        </button>

                        <button
                            onClick={handleSaveGoogle}
                            disabled={saving || (!googleApiKey && !googleCxId)}
                            className="btn-primary flex items-center gap-2 text-sm py-2 disabled:opacity-50"
                        >
                            {saving ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Save className="w-4 h-4" />
                            )}
                            儲存
                        </button>

                        {googleTestResult && (
                            <span className={`flex items-center gap-1 text-sm ${googleTestResult.success ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                }`}>
                                {googleTestResult.success ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                                {googleTestResult.message}
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* AI Hub */}
            <div className="card">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-green-50 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                        <Cpu className="w-5 h-5 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                        <h2 className="font-semibold text-gray-900 dark:text-gray-100">AI Hub</h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400">統一 AI 服務介面，支援多個提供者和模型</p>
                    </div>
                    <div className="ml-auto">
                        {settings?.has_ai_api ? (
                            <span className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                                <CheckCircle2 className="w-4 h-4" /> 已設定
                            </span>
                        ) : (
                            <span className="flex items-center gap-1 text-gray-400 text-sm">
                                <XCircle className="w-4 h-4" /> 未設定
                            </span>
                        )}
                    </div>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            AI 提供者
                        </label>
                        <select
                            value={aiProvider}
                            onChange={(e) => setAiProvider(e.target.value)}
                            className="input"
                        >
                            {Object.entries(providers).map(([key, provider]) => (
                                <option key={key} value={key}>
                                    {provider.name} - {provider.description}
                                </option>
                            ))}
                        </select>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            選擇 AI 服務提供者
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            AI 模型
                        </label>
                        <select
                            value={aiModel}
                            onChange={(e) => setAiModel(e.target.value)}
                            className="input"
                        >
                            {Object.entries(models).map(([key, model]) => (
                                <option key={key} value={key}>
                                    {key} - {model.description}
                                </option>
                            ))}
                        </select>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            選擇要使用的 AI 模型
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            API Key {settings?.ai_api_key && <span className="text-gray-400">({settings.ai_api_key})</span>}
                        </label>
                        <div className="relative">
                            <input
                                type={showAiKey ? 'text' : 'password'}
                                value={aiApiKey}
                                onChange={(e) => setAiApiKey(e.target.value)}
                                placeholder="輸入新的 API Key..."
                                className="input pr-10"
                            />
                            <button
                                type="button"
                                onClick={() => setShowAiKey(!showAiKey)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                            >
                                {showAiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                            </button>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {aiProvider === 'zeabur' ? 'Zeabur AI Hub API Key (格式: sk-...)' : 'Google AI Studio API Key'}
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <button
                            onClick={testAiHub}
                            disabled={testingAi}
                            className="btn-secondary flex items-center gap-2 text-sm py-2 disabled:opacity-50"
                        >
                            {testingAi ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <TestTube className="w-4 h-4" />
                            )}
                            測試連線
                        </button>

                        <button
                            onClick={handleSaveAI}
                            disabled={saving || !aiApiKey}
                            className="btn-primary flex items-center gap-2 text-sm py-2 disabled:opacity-50"
                        >
                            {saving ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Save className="w-4 h-4" />
                            )}
                            儲存
                        </button>

                        {aiTestResult && (
                            <span className={`flex items-center gap-1 text-sm ${aiTestResult.success ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                }`}>
                                {aiTestResult.success ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                                {aiTestResult.message}
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* Google OAuth (Optional) */}
            <div className="card">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-purple-50 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                        <Key className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                        <h2 className="font-semibold text-gray-900 dark:text-gray-100">Google OAuth</h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400">用於 Google 帳號登入（可選）</p>
                    </div>
                    <div className="ml-auto">
                        {settings?.has_google_oauth ? (
                            <span className="flex items-center gap-1 text-green-600 dark:text-green-400 text-sm">
                                <CheckCircle2 className="w-4 h-4" /> 已設定
                            </span>
                        ) : (
                            <span className="flex items-center gap-1 text-gray-400 text-sm">
                                <XCircle className="w-4 h-4" /> 未設定
                            </span>
                        )}
                    </div>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Client ID {settings?.google_client_id && <span className="text-gray-400">({settings.google_client_id})</span>}
                        </label>
                        <input
                            type="text"
                            value={googleClientId}
                            onChange={(e) => setGoogleClientId(e.target.value)}
                            placeholder="輸入 Client ID..."
                            className="input"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Client Secret {settings?.google_client_secret && <span className="text-gray-400">({settings.google_client_secret})</span>}
                        </label>
                        <div className="relative">
                            <input
                                type={showOAuthSecret ? 'text' : 'password'}
                                value={googleClientSecret}
                                onChange={(e) => setGoogleClientSecret(e.target.value)}
                                placeholder="輸入 Client Secret..."
                                className="input pr-10"
                            />
                            <button
                                type="button"
                                onClick={() => setShowOAuthSecret(!showOAuthSecret)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                            >
                                {showOAuthSecret ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                            </button>
                        </div>
                    </div>

                    <div className="flex justify-end pt-2">
                        <button
                            onClick={handleSaveOAuth}
                            disabled={saving || (!googleClientId && !googleClientSecret)}
                            className="btn-primary flex items-center gap-2 text-sm py-2 disabled:opacity-50"
                        >
                            {saving ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Save className="w-4 h-4" />
                            )}
                            儲存
                        </button>
                    </div>
                </div>
            </div>

            {/* Demo Data Seeding */}
            <div className="card border border-amber-200 dark:border-amber-900/30 bg-amber-50/5 dark:bg-amber-950/5">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-amber-50 dark:bg-amber-900/30 rounded-lg flex items-center justify-center">
                        <Database className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                    </div>
                    <div>
                        <h2 className="font-semibold text-gray-900 dark:text-gray-100">演示展示數據 (Demo Seeding)</h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400">一鍵預置「新站模式」與「舊站模式」專案，供功能展示使用</p>
                    </div>
                </div>

                <div className="space-y-4">
                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                        點擊下方按鈕後，系統將一鍵清空現有專案資料庫，並自動預置完整的演示資料。包含網站定位、主題地圖節點、已被核准的 Brief，以及已撰寫完成並通過 AI 品質審查的草稿等。
                    </p>
                    
                    {seedSuccess && (
                        <div className="p-3 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 rounded-lg text-emerald-700 dark:text-emerald-400 text-sm">
                            {seedSuccess} 系統將在 1.5 秒後自動重新載入...
                        </div>
                    )}

                    <div className="flex justify-start">
                        <button
                            onClick={handleSeedDemo}
                            disabled={seeding}
                            className="btn bg-amber-600 hover:bg-amber-700 text-white flex items-center gap-2 text-sm py-2.5 px-4 disabled:opacity-50 font-medium rounded-lg shadow-sm hover:shadow transition-all duration-200"
                        >
                            {seeding ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Database className="w-4 h-4" />
                            )}
                            一鍵預置展示數據
                        </button>
                    </div>
                </div>
            </div>

            {/* Removed global Save Button - each section now has its own */}
        </div>
    )
}

export default Settings
