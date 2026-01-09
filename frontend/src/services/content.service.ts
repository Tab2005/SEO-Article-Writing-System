import api from './api'
import { ArticleOutline } from '../types/content.types'

export interface OutlineRequest {
    topic: string
    target_keyword: string
    word_count_target?: number
    tone?: string
    use_competitor_analysis?: boolean
    market?: string
}

export interface ContentRequest {
    topic: string
    target_keyword: string
    word_count_target?: number
    tone?: string
    market?: string
}

export interface ContentResponse {
    outline: ArticleOutline
    content: string
    word_count: number
    target_keyword: string
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
    }
}
