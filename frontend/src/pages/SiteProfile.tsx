import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldAlert, Award, Compass, Eye, Save, Sparkles, Briefcase, CheckCircle } from 'lucide-react'
import { planningService, SiteProfile } from '../services/planning.service'
import { useProjectStore } from '../store/projectStore'

function SiteProfilePage() {
    const navigate = useNavigate()
    const { currentProject, setCurrentProject } = useProjectStore()
    const [profile, setProfile] = useState<SiteProfile | null>(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [summarizing, setSummarizing] = useState(false)
    const [successMessage, setSuccessMessage] = useState('')

    // Form inputs
    const [siteName, setSiteName] = useState('')
    const [businessType, setBusinessType] = useState('')
    const [siteDescription, setSiteDescription] = useState('')
    const [targetAudiences, setTargetAudiences] = useState<string>('')
    const [productsOrServices, setProductsOrServices] = useState<string>('')
    const [coreTopics, setCoreTopics] = useState<string>('')
    const [allowedAngles, setAllowedAngles] = useState<string>('')
    const [restrictedAngles, setRestrictedAngles] = useState<string>('')
    const [brandVoice, setBrandVoice] = useState('')
    const [proofAssets, setProofAssets] = useState<string>('')
    const [primaryGoals, setPrimaryGoals] = useState<string>('')
    const [geoFocus, setGeoFocus] = useState<string>('')
    const [industryConstraints, setIndustryConstraints] = useState<string>('')
    const [editorialNotes, setEditorialNotes] = useState('')

    useEffect(() => {
        if (!currentProject) return
        loadProfile()
    }, [currentProject])

    const loadProfile = async () => {
        try {
            setLoading(true)
            const data = await planningService.getSiteProfile(currentProject!.id)
            setProfile(data)
            // Initialize form states
            setSiteName(data.site_name || '')
            setBusinessType(data.business_type || '')
            setSiteDescription(data.site_description || '')
            setTargetAudiences(data.target_audiences?.join('\n') || '')
            setProductsOrServices(data.products_or_services?.join('\n') || '')
            setCoreTopics(data.core_topics?.join('\n') || '')
            setAllowedAngles(data.allowed_angles?.join('\n') || '')
            setRestrictedAngles(data.restricted_angles?.join('\n') || '')
            setBrandVoice(data.brand_voice || '')
            setProofAssets(data.proof_assets?.join('\n') || '')
            setPrimaryGoals(data.primary_goals?.join('\n') || '')
            setGeoFocus(data.geo_focus?.join('\n') || '')
            setIndustryConstraints(data.industry_constraints?.join('\n') || '')
            setEditorialNotes(data.editorial_notes || '')
        } catch (err: any) {
            if (err.response?.status === 404) {
                // Not created yet, reset form
                setProfile(null)
                setSiteName('')
                setBusinessType('')
                setSiteDescription('')
                setTargetAudiences('')
                setProductsOrServices('')
                setCoreTopics('')
                setAllowedAngles('')
                setRestrictedAngles('')
                setBrandVoice('')
                setProofAssets('')
                setPrimaryGoals('')
                setGeoFocus('')
                setIndustryConstraints('')
                setEditorialNotes('')
            } else {
                console.error('Failed to load site profile:', err)
            }
        } finally {
            setLoading(false)
        }
    }

    const splitTextarea = (val: string): string[] => {
        return val.split('\n').map(item => item.trim()).filter(item => item !== '')
    }

    const handleSave = async () => {
        if (!currentProject) return
        if (!siteName.trim()) {
            alert('請至少填寫網站名稱！')
            return
        }
        try {
            setSaving(true)
            const payload: Partial<SiteProfile> = {
                site_name: siteName,
                business_type: businessType || undefined,
                site_description: siteDescription || undefined,
                target_audiences: splitTextarea(targetAudiences),
                products_or_services: splitTextarea(productsOrServices),
                core_topics: splitTextarea(coreTopics),
                allowed_angles: splitTextarea(allowedAngles),
                restricted_angles: splitTextarea(restrictedAngles),
                brand_voice: brandVoice || undefined,
                proof_assets: splitTextarea(proofAssets),
                primary_goals: splitTextarea(primaryGoals),
                geo_focus: splitTextarea(geoFocus),
                industry_constraints: splitTextarea(industryConstraints),
                editorial_notes: editorialNotes || undefined,
                status: 'draft' // Will be auto-evaluated to "ready" by backend if name, type and desc are filled
            }

            const saved = await planningService.saveSiteProfile(currentProject.id, payload)
            setProfile(saved)
            
            // Check if project status changed on backend
            // Reload project info to sync layout
            const updatedProject = await planningService.getProject(currentProject.id)
            setCurrentProject(updatedProject)

            setSuccessMessage(saved.status === 'ready' 
                ? '定位已成功儲存！定位狀態：已完備 (Ready)。' 
                : '定位已成功儲存！定位狀態：草稿。請填完 網站名稱、商業類型 與 描述 以使定位完備。'
            )
            setTimeout(() => setSuccessMessage(''), 4000)
        } catch (err) {
            console.error('Failed to save profile:', err)
            alert('儲存失敗，請重試。')
        } finally {
            setSaving(false)
        }
    }

    const handleSummarize = async () => {
        if (!currentProject || !profile) return
        try {
            setSummarizing(true)
            const updated = await planningService.summarizeSiteProfile(currentProject.id)
            setProfile(updated)
            setSuccessMessage('AI 品牌定位摘要已成功生成！')
            setTimeout(() => setSuccessMessage(''), 3000)
        } catch (err: any) {
            console.error('Failed to generate snapshot:', err)
            alert(err.response?.data?.detail || 'AI 生成摘要失敗，請填寫完整資訊後再重試。')
        } finally {
            setSummarizing(false)
        }
    }

    if (!currentProject) {
        return (
            <div className="card text-center py-16">
                <Compass className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">未選定專案</h3>
                <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-6 text-sm">
                    請先至專案管理頁面選擇或建立一個專案，再進行網站定位。
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
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                        網站身份定位 (Site Profile)
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        目前專案：<span className="font-semibold text-primary-600 dark:text-primary-400">{currentProject.name}</span>
                        {profile?.status === 'ready' ? (
                            <span className="ml-3 inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-green-50 text-green-600 font-medium">
                                <CheckCircle className="w-3.5 h-3.5" /> 定位已完備 (Ready)
                            </span>
                        ) : (
                            <span className="ml-3 inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-gray-100 dark:bg-slate-700 text-gray-500 font-medium">
                                定位未完備 (Draft)
                            </span>
                        )}
                    </p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="btn-primary flex items-center justify-center gap-2"
                    >
                        <Save className="w-5 h-5" />
                        {saving ? '儲存中...' : '儲存定位'}
                    </button>
                </div>
            </div>

            {successMessage && (
                <div className="p-4 bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-400 rounded-xl border border-green-200 dark:border-green-800/30 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5" />
                    <span className="text-sm font-medium">{successMessage}</span>
                </div>
            )}

            {loading ? (
                <div className="text-center py-12 text-gray-500">載入中...</div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left: Interactive Editor */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Section 1: Basic Identity */}
                        <div className="card space-y-4">
                            <div className="flex items-center gap-2 pb-3 border-b border-gray-100 dark:border-slate-700">
                                <Briefcase className="w-5 h-5 text-primary-600" />
                                <h3 className="font-semibold text-gray-900 dark:text-gray-100">核心身份 (必填)</h3>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        網站名稱 *
                                    </label>
                                    <input
                                        type="text"
                                        value={siteName}
                                        onChange={(e) => setSiteName(e.target.value)}
                                        className="input"
                                        placeholder="例如：電商成長指南"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        商業類型 / 站點類別 *
                                    </label>
                                    <input
                                        type="text"
                                        value={businessType}
                                        onChange={(e) => setBusinessType(e.target.value)}
                                        className="input"
                                        placeholder="例如：SaaS 企業部落格、電商官網、技術論壇"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    網站描述 *
                                </label>
                                <textarea
                                    value={siteDescription}
                                    onChange={(e) => setSiteDescription(e.target.value)}
                                    className="input"
                                    rows={3}
                                    placeholder="描述網站核心定位，例如：專門為中小企業提供 Shopify 電商營運、數位廣告與 SEO 行銷策略的教學網誌。"
                                />
                            </div>
                        </div>

                        {/* Section 2: Core Targets & Topics */}
                        <div className="card space-y-4">
                            <div className="flex items-center gap-2 pb-3 border-b border-gray-100 dark:border-slate-700">
                                <Award className="w-5 h-5 text-primary-600" />
                                <h3 className="font-semibold text-gray-900 dark:text-gray-100">目標受眾與業務定位</h3>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        目標受眾 (每行一個)
                                    </label>
                                    <textarea
                                        value={targetAudiences}
                                        onChange={(e) => setTargetAudiences(e.target.value)}
                                        className="input text-sm"
                                        rows={4}
                                        placeholder="電商創業者&#10;行銷經理&#10;Shopify 站長"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        產品或服務 (每行一個)
                                    </label>
                                    <textarea
                                        value={productsOrServices}
                                        onChange={(e) => setProductsOrServices(e.target.value)}
                                        className="input text-sm"
                                        rows={4}
                                        placeholder="電商行銷顧問課程&#10;行銷自動化外掛工具"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        核心寫作主題領域 (每行一個)
                                    </label>
                                    <textarea
                                        value={coreTopics}
                                        onChange={(e) => setCoreTopics(e.target.value)}
                                        className="input text-sm"
                                        rows={4}
                                        placeholder="電商 SEO 機制&#10;Shopify 佈景主題優化&#10;GA4 流量分析教學"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        品牌語調 / 風格特色
                                    </label>
                                    <input
                                        type="text"
                                        value={brandVoice}
                                        onChange={(e) => setBrandVoice(e.target.value)}
                                        className="input"
                                        placeholder="專業、親切、注重數據、簡明易懂"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Section 3: Content Strategy & Boundaries */}
                        <div className="card space-y-4">
                            <div className="flex items-center gap-2 pb-3 border-b border-gray-100 dark:border-slate-700">
                                <ShieldAlert className="w-5 h-5 text-primary-600" />
                                <h3 className="font-semibold text-gray-900 dark:text-gray-100">內容寫作切角與邊界</h3>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 text-green-600 dark:text-green-400">
                                        推薦切角 (Allowed Angles, 每行一個)
                                    </label>
                                    <textarea
                                        value={allowedAngles}
                                        onChange={(e) => setAllowedAngles(e.target.value)}
                                        className="input text-sm"
                                        rows={4}
                                        placeholder="實戰案例分析&#10;數據佐證的教學指南&#10;新手友好的步驟拆解"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 text-red-500">
                                        禁用切角 / 敏感詞 (Restricted Angles, 每行一個)
                                    </label>
                                    <textarea
                                        value={restrictedAngles}
                                        onChange={(e) => setRestrictedAngles(e.target.value)}
                                        className="input text-sm"
                                        rows={4}
                                        placeholder="違法黑帽 SEO 技巧&#10;醫療診斷建議&#10;未經證實的八卦"
                                    />
                                    <p className="text-xs text-gray-400 mt-1">
                                        評估引擎會以此名單進行硬性攔截過濾。
                                    </p>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        佐證資產 / E-E-A-T 憑證 (每行一個)
                                    </label>
                                    <textarea
                                        value={proofAssets}
                                        onChange={(e) => setProofAssets(e.target.value)}
                                        className="input text-sm"
                                        rows={3}
                                        placeholder="擁有 10 年 Shopify 電商操盤經驗的顧問團隊&#10;榮獲 2024 年最佳行銷部落格大獎"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        主要商業目標 (每行一個)
                                    </label>
                                    <textarea
                                        value={primaryGoals}
                                        onChange={(e) => setPrimaryGoals(e.target.value)}
                                        className="input text-sm"
                                        rows={3}
                                        placeholder="獲取顧問諮詢 Leads&#10;提高工具訂閱註冊數"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        地理焦點 / 地域限制 (每行一個)
                                    </label>
                                    <input
                                        type="text"
                                        value={geoFocus}
                                        onChange={(e) => setGeoFocus(e.target.value)}
                                        className="input"
                                        placeholder="例如：台灣、香港、星馬地區"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        行業規範與限制 (每行一個)
                                    </label>
                                    <input
                                        type="text"
                                        value={industryConstraints}
                                        onChange={(e) => setIndustryConstraints(e.target.value)}
                                        className="input"
                                        placeholder="例如：不涉及個人理財推薦、無版權疑慮之原創圖片"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    編輯備註說明
                                </label>
                                <textarea
                                    value={editorialNotes}
                                    onChange={(e) => setEditorialNotes(e.target.value)}
                                    className="input"
                                    rows={2}
                                    placeholder="其他寫作規範或注意事項..."
                                />
                            </div>
                        </div>
                    </div>

                    {/* Right: AI Brand Snapshot Summary */}
                    <div className="space-y-6">
                        <div className="card space-y-4 sticky top-6">
                            <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-slate-700">
                                <div className="flex items-center gap-2">
                                    <Sparkles className="w-5 h-5 text-primary-600 animate-pulse" />
                                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">AI 定位快照摘要</h3>
                                </div>
                                <button
                                    onClick={handleSummarize}
                                    disabled={summarizing || !profile}
                                    className="text-xs px-2.5 py-1.5 bg-primary-50 dark:bg-primary-900/30 hover:bg-primary-100 text-primary-600 dark:text-primary-400 rounded-lg font-medium transition-colors disabled:opacity-50"
                                >
                                    {summarizing ? '生成中...' : '重新生成'}
                                </button>
                            </div>

                            {profile?.summary_snapshot ? (
                                <div className="space-y-4">
                                    <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-lg text-sm text-gray-700 dark:text-gray-300 leading-relaxed border border-gray-100 dark:border-slate-700">
                                        {profile.summary_snapshot}
                                    </div>
                                    <p className="text-xs text-gray-400 text-right">
                                        快照將作為 LLM 題目評估的全局品牌背景。
                                    </p>
                                </div>
                            ) : (
                                <div className="text-center py-12 text-gray-400">
                                    <Eye className="w-10 h-10 mx-auto text-gray-300 mb-2" />
                                    <p className="text-sm">尚未生成品牌定位快照。</p>
                                    <p className="text-xs mt-1">請先「儲存定位」後，點擊右上方「重新生成」按鈕。</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default SiteProfilePage
