import api from './api'

export interface Project {
    id: string
    name: string
    description?: string
    target_market?: string
    mode: 'new_site' | 'existing_site'
    status: 'draft' | 'active'
    domain?: string
    articleCount?: number
    created_at: string
    updated_at: string
}

export interface SiteProfile {
    id?: string
    project_id?: string
    site_name: string
    business_type?: string
    site_description?: string
    target_audiences?: string[]
    products_or_services?: string[]
    core_topics?: string[]
    allowed_angles?: string[]
    restricted_angles?: string[]
    brand_voice?: string
    proof_assets?: string[]
    primary_goals?: string[]
    geo_focus?: string[]
    industry_constraints?: string[]
    editorial_notes?: string
    status: 'draft' | 'ready'
    summary_snapshot?: string
    created_at?: string
    updated_at?: string
}

export interface TopicNode {
    id: string
    project_id: string
    parent_id?: string
    name: string
    topic_role: 'pillar' | 'supporting' | 'bridge' | 'comparison' | 'decision' | 'faq'
    description?: string
    journey_stage?: 'awareness' | 'consideration' | 'decision'
    priority: 'high' | 'medium' | 'low'
    supports?: string[]
    supported_by?: string[]
    status: 'draft' | 'active' | 'archived'
    sort_order: number
    created_at: string
    updated_at: string
    children?: TopicNode[]
}

export interface ContentItem {
    id: string
    project_id: string
    title: string
    url?: string
    content_type: string
    mapped_topic_id?: string
    journey_stage?: string
    status: 'imported' | 'mapped' | 'archived'
    notes?: string
    created_at: string
    updated_at: string
}

export interface QualificationResult {
    id: string
    project_id: string
    input_term: string
    decision: 'qualified' | 'rewrite_existing' | 'not_qualified'
    summary_reason?: string
    mapped_topic_id?: string
    suggested_angle?: string
    target_journey_stage?: string
    identity_fit?: string
    topic_fit?: string
    audience_fit?: string
    authority_fit?: string
    business_fit?: string
    overlap_risk?: string
    boundary_risk?: string
    risks?: string[]
    alternative_topics?: string[]
    recommended_next_step?: string
    review_status: 'generated' | 'approved' | 'rejected' | 'edited'
    created_at: string
}

export interface ArticleBrief {
    id: string
    project_id: string
    qualification_id?: string
    mapped_topic_id?: string
    title_direction: string
    article_role?: string
    search_intent?: string
    target_audience?: string
    primary_question?: string
    next_question?: string
    info_gain_requirement?: string
    restricted_content?: string
    recommended_internal_links?: string
    cta_direction?: string
    status: string // 'draft' | 'approved' | 'rejected' 等
    created_at: string
    updated_at: string
}

export const planningService = {
    // Projects API
    listProjects: async (): Promise<Project[]> => {
        const response = await api.get<Project[]>('/projects')
        return response.data
    },
    createProject: async (data: Partial<Project>): Promise<Project> => {
        const response = await api.post<Project>('/projects', data)
        return response.data
    },
    getProject: async (projectId: string): Promise<Project> => {
        const response = await api.get<Project>(`/projects/${projectId}`)
        return response.data
    },
    updateProject: async (projectId: string, data: Partial<Project>): Promise<Project> => {
        const response = await api.patch<Project>(`/projects/${projectId}`, data)
        return response.data
    },
    deleteProject: async (projectId: string): Promise<void> => {
        await api.delete(`/projects/${projectId}`)
    },
    activateProject: async (projectId: string): Promise<Project> => {
        const response = await api.post<Project>(`/projects/${projectId}/activate`)
        return response.data
    },

    // Site Profile API
    getSiteProfile: async (projectId: string): Promise<SiteProfile> => {
        const response = await api.get<SiteProfile>(`/projects/${projectId}/site-profile`)
        return response.data
    },
    saveSiteProfile: async (projectId: string, data: Partial<SiteProfile>): Promise<SiteProfile> => {
        const response = await api.put<SiteProfile>(`/projects/${projectId}/site-profile`, data)
        return response.data
    },
    updateSiteProfile: async (projectId: string, data: Partial<SiteProfile>): Promise<SiteProfile> => {
        const response = await api.patch<SiteProfile>(`/projects/${projectId}/site-profile`, data)
        return response.data
    },
    summarizeSiteProfile: async (projectId: string): Promise<SiteProfile> => {
        const response = await api.post<SiteProfile>(`/projects/${projectId}/site-profile/summarize`)
        return response.data
    },

    // Topic Map API
    getTopicNodes: async (projectId: string, tree: boolean = false): Promise<TopicNode[]> => {
        const response = await api.get<TopicNode[]>(`/projects/${projectId}/topic-nodes`, {
            params: { tree }
        })
        return response.data
    },
    createTopicNode: async (projectId: string, data: Partial<TopicNode>): Promise<TopicNode> => {
        const response = await api.post<TopicNode>(`/projects/${projectId}/topic-nodes`, data)
        return response.data
    },
    updateTopicNode: async (projectId: string, nodeId: string, data: Partial<TopicNode>): Promise<TopicNode> => {
        const response = await api.patch<TopicNode>(`/projects/${projectId}/topic-nodes/${nodeId}`, data)
        return response.data
    },
    moveTopicNode: async (projectId: string, nodeId: string, parentId: string | null): Promise<TopicNode> => {
        const response = await api.post<TopicNode>(`/projects/${projectId}/topic-nodes/${nodeId}/move`, {
            parent_id: parentId
        })
        return response.data
    },
    archiveTopicNode: async (projectId: string, nodeId: string): Promise<TopicNode> => {
        const response = await api.post<TopicNode>(`/projects/${projectId}/topic-nodes/${nodeId}/archive`)
        return response.data
    },
    getTopicMapGaps: async (projectId: string): Promise<any[]> => {
        const response = await api.get<any[]>(`/projects/${projectId}/topic-map/gaps`)
        return response.data
    },

    // Content Library API
    importContentItems: async (projectId: string, items: { title: string; url?: string; content_type?: string; notes?: string }[]): Promise<ContentItem[]> => {
        const response = await api.post<ContentItem[]>(`/projects/${projectId}/content-items/import`, { items })
        return response.data
    },
    getContentItems: async (projectId: string, mapped?: boolean): Promise<ContentItem[]> => {
        const response = await api.get<ContentItem[]>(`/projects/${projectId}/content-items`, {
            params: { mapped }
        })
        return response.data
    },
    updateContentItem: async (projectId: string, itemId: string, data: Partial<ContentItem>): Promise<ContentItem> => {
        const response = await api.patch<ContentItem>(`/projects/${projectId}/content-items/${itemId}`, data)
        return response.data
    },
    mapContentItem: async (projectId: string, itemId: string, mappedTopicId: string | null): Promise<ContentItem> => {
        const response = await api.post<ContentItem>(`/projects/${projectId}/content-items/${itemId}/map-topic`, {
            mapped_topic_id: mappedTopicId
        })
        return response.data
    },

    // Qualification API
    evaluateTopic: async (projectId: string, inputTerm: string): Promise<QualificationResult> => {
        const response = await api.post<QualificationResult>(`/projects/${projectId}/qualification-results`, {
            input_term: inputTerm
        })
        return response.data
    },
    getQualificationResults: async (projectId: string): Promise<QualificationResult[]> => {
        const response = await api.get<QualificationResult[]>(`/projects/${projectId}/qualification-results`)
        return response.data
    },
    getQualificationResult: async (projectId: string, resultId: string): Promise<QualificationResult> => {
        const response = await api.get<QualificationResult>(`/projects/${projectId}/qualification-results/${resultId}`)
        return response.data
    },
    updateQualificationResult: async (projectId: string, resultId: string, data: Partial<QualificationResult>): Promise<QualificationResult> => {
        const response = await api.patch<QualificationResult>(`/projects/${projectId}/qualification-results/${resultId}`, data)
        return response.data
    },

    // Article Briefs API
    listBriefs: async (projectId: string): Promise<ArticleBrief[]> => {
        const response = await api.get<ArticleBrief[]>(`/projects/${projectId}/briefs`)
        return response.data
    },
    createBrief: async (projectId: string, data: Partial<ArticleBrief>): Promise<ArticleBrief> => {
        const response = await api.post<ArticleBrief>(`/projects/${projectId}/briefs`, data)
        return response.data
    },
    createBriefFromQualification: async (projectId: string, qualificationId: string): Promise<ArticleBrief> => {
        const response = await api.post<ArticleBrief>(`/projects/${projectId}/briefs/from-qualification/${qualificationId}`)
        return response.data
    },
    getBrief: async (projectId: string, briefId: string): Promise<ArticleBrief> => {
        const response = await api.get<ArticleBrief>(`/projects/${projectId}/briefs/${briefId}`)
        return response.data
    },
    updateBrief: async (projectId: string, briefId: string, data: Partial<ArticleBrief>): Promise<ArticleBrief> => {
        const response = await api.patch<ArticleBrief>(`/projects/${projectId}/briefs/${briefId}`, data)
        return response.data
    },
    deleteBrief: async (projectId: string, briefId: string): Promise<void> => {
        await api.delete(`/projects/${projectId}/briefs/${briefId}`)
    }
}

