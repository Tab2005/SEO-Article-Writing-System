import { useState, useEffect } from 'react'
import {
    Settings as SettingsIcon, Save, TestTube, CheckCircle2,
    XCircle, Loader2, Eye, EyeOff, Key, Globe, Bot
} from 'lucide-react'
import api from '../services/api'

interface SettingsData {
    google_api_key: string
    google_cx_id: string
    openai_api_key: string
    google_client_id: string
    google_client_secret: string
    has_google_api: boolean
    has_openai_api: boolean
    has_google_oauth: boolean
}

interface TestResult {
    service: string
    success: boolean
    message: string
}

function Settings() {
    const [settings, setSettings] = useState<SettingsData | null>(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)

    // Form fields
    const [googleApiKey, setGoogleApiKey] = useState('')
    const [googleCxId, setGoogleCxId] = useState('')
    const [openaiApiKey, setOpenaiApiKey] = useState('')
    const [googleClientId, setGoogleClientId] = useState('')
    const [googleClientSecret, setGoogleClientSecret] = useState('')

    // Show/hide toggles
    const [showGoogleKey, setShowGoogleKey] = useState(false)
    const [showOpenaiKey, setShowOpenaiKey] = useState(false)
    const [showOAuthSecret, setShowOAuthSecret] = useState(false)

    // Test results
    const [testingGoogle, setTestingGoogle] = useState(false)
    const [testingOpenai, setTestingOpenai] = useState(false)
    const [googleTestResult, setGoogleTestResult] = useState<TestResult | null>(null)
    const [openaiTestResult, setOpenaiTestResult] = useState<TestResult | null>(null)

    // Fetch current settings
    useEffect(() => {
        fetchSettings()
    }, [])

    const fetchSettings = async () => {
        try {
            const response = await api.get<SettingsData>('/settings')
            setSettings(response.data)
        } catch (err: any) {
            setError('無法載入設定')
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async () => {
        setSaving(true)
        setError(null)
        setSuccess(null)

        try {
            await api.put('/settings', {
                google_api_key: googleApiKey || undefined,
                google_cx_id: googleCxId || undefined,
                openai_api_key: openaiApiKey || undefined,
                google_client_id: googleClientId || undefined,
                google_client_secret: googleClientSecret || undefined,
            })

            // Clear form fields
            setGoogleApiKey('')
            setGoogleCxId('')
            setOpenaiApiKey('')
            setGoogleClientId('')
            setGoogleClientSecret('')

            // Refresh settings
            await fetchSettings()
            setSuccess('設定已儲存成功！')
        } catch (err: any) {
            setError(err.response?.data?.detail || '儲存失敗')
        } finally {
            setSaving(false)
        }
    }

    const testGoogleSearch = async () => {
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

    const testOpenai = async () => {
        setTestingOpenai(true)
        setOpenaiTestResult(null)

        try {
            const response = await api.post<TestResult>('/settings/test/openai')
            setOpenaiTestResult(response.data)
        } catch (err: any) {
            setOpenaiTestResult({
                service: 'OpenAI',
                success: false,
                message: '測試請求失敗',
            })
        } finally {
            setTestingOpenai(false)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
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

            {/* OpenAI API */}
            <div className="card">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-green-50 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                        <Bot className="w-5 h-5 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                        <h2 className="font-semibold text-gray-900 dark:text-gray-100">OpenAI API</h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400">用於 AI 內容生成</p>
                    </div>
                    <div className="ml-auto">
                        {settings?.has_openai_api ? (
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
                            API Key {settings?.openai_api_key && <span className="text-gray-400">({settings.openai_api_key})</span>}
                        </label>
                        <div className="relative">
                            <input
                                type={showOpenaiKey ? 'text' : 'password'}
                                value={openaiApiKey}
                                onChange={(e) => setOpenaiApiKey(e.target.value)}
                                placeholder="輸入新的 API Key (sk-...)..."
                                className="input pr-10"
                            />
                            <button
                                type="button"
                                onClick={() => setShowOpenaiKey(!showOpenaiKey)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                            >
                                {showOpenaiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                            </button>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <button
                            onClick={testOpenai}
                            disabled={testingOpenai}
                            className="btn-secondary flex items-center gap-2 text-sm py-2 disabled:opacity-50"
                        >
                            {testingOpenai ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <TestTube className="w-4 h-4" />
                            )}
                            測試連線
                        </button>

                        {openaiTestResult && (
                            <span className={`flex items-center gap-1 text-sm ${openaiTestResult.success ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                }`}>
                                {openaiTestResult.success ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                                {openaiTestResult.message}
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
                </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end">
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="btn-primary flex items-center gap-2 disabled:opacity-50"
                >
                    {saving ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                        <Save className="w-5 h-5" />
                    )}
                    儲存設定
                </button>
            </div>
        </div>
    )
}

export default Settings
