import api from './api'
import { ArticleOutline } from '../types/content.types'

export interface OutlineRequest {
    topic: string
    target_keyword: string
    secondary_keywords?: string[]
    word_count_target?: number
    tone?: string
    use_competitor_analysis?: boolean
    market?: string
    brief_id?: string
}

export interface ContentRequest {
    topic: string
    target_keyword: string
    secondary_keywords?: string[]
    word_count_target?: number
    tone?: string
    market?: string
    brief_id?: string
    outline?: ArticleOutline
}

export interface ContentResponse {
    outline: ArticleOutline
    content: string
    word_count: number
    target_keyword: string
    secondary_keywords?: string[]
}

export const contentService = {
    /**
     * Generate article outline
     */
    async generateOutline(request: OutlineRequest): Promise<ArticleOutline> {
        const response = await api.post<ArticleOutline>('/content/outline', request)
        return response.data
    },

    /**
     * Generate full article content
     */
    async generateContent(request: ContentRequest): Promise<ContentResponse> {
        const response = await api.post<ContentResponse>('/content/generate', request)
        return response.data
    },

    /**
     * Optimize existing content
     */
    async optimizeContent(content: string, targetKeywords: string[]): Promise<{ content: string }> {
        const response = await api.post('/content/optimize', {
            content,
            target_keywords: targetKeywords
        })
        return response.data
    },

    /**
     * Run QA check on a draft
     */
    async runQA(draftId: string): Promise<any> {
        const response = await api.post(`/content/draft/${draftId}/qa`)
        return response.data
    },

    /**
     * Get content queue for a project
     */
    async getContentQueue(projectId: string): Promise<any[]> {
        const response = await api.get(`/projects/${projectId}/content-queue`)
        return response.data
    },

    /**
     * Get draft version history
     */
    async getDraftVersions(draftId: string): Promise<any[]> {
        const response = await api.get(`/content/draft/${draftId}/versions`)
        return response.data
    },

    /**
     * Save current draft content as a new version
     */
    async saveNewVersion(draftId: string): Promise<any> {
        const response = await api.post(`/content/draft/${draftId}/save-version`)
        return response.data
    },

    /**
     * Rollback a draft to a specific version
     */
    async rollbackVersion(draftId: string, versionId: string): Promise<any> {
        const response = await api.post(`/content/draft/${draftId}/versions/${versionId}/rollback`)
        return response.data
    },

    /**
     * Seed demo project data
     */
    async seedDemo(): Promise<any> {
        const response = await api.post('/projects/seed-demo')
        return response.data
    }
}

