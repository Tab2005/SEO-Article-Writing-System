import api from './api'

export interface LsiKeyword {
    term: string
    weight: number
    essential: boolean
    source: string
}

export interface SuggestedIntent {
    value: string
    label: string
    description: string
    confidence: number
}

export interface StrategyPack {
    keyword: string
    market: string
    ai_detected_intent: string
    suggested_intents: SuggestedIntent[]
    suggested_tones: string[]
    suggested_titles: string[]
    lsi_keywords: LsiKeyword[]
    eeat_tips: string[]
    competitor_insights?: {
        count: number
        avg_word_count: number
    }
}

export interface StrategyRequest {
    keyword: string
    market?: string
    job_id?: string
    intent?: string
    tone?: string
    regenerate_titles?: boolean
}

export const strategyService = {
    /**
     * Generate strategy pack for content creation.
     * 
     * Returns AI-detected intent, suggested titles, LSI keywords, and E-E-A-T tips.
     */
    async getStrategyPack(request: StrategyRequest): Promise<StrategyPack> {
        const response = await api.post<StrategyPack>('/content/strategy', request)
        return response.data
    },

    /**
     * Regenerate titles with different intent/tone.
     * 
     * Convenience method that sets regenerate_titles=true.
     */
    async regenerateTitles(
        keyword: string,
        intent: string,
        tone: string,
        jobId?: string
    ): Promise<StrategyPack> {
        return this.getStrategyPack({
            keyword,
            intent,
            tone,
            job_id: jobId,
            regenerate_titles: true,
        })
    }
}
