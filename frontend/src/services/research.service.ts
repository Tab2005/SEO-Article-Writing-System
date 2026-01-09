import api from './api'

export interface SerpResult {
    rank: number
    title: string
    url: string
    snippet: string
    scraped_at?: string
}

export interface HeadingStructure {
    h1: string[]
    h2: string[]
    h3: string[]
}

export interface CompetitorData {
    rank: number
    url: string
    title: string
    word_count: number
    headings: HeadingStructure
    meta_description?: string
    meta_keywords?: string
    scraped_at: string
}

export interface AnalysisReport {
    keyword: string
    market: string
    avg_word_count: number
    min_word_count: number
    max_word_count: number
    common_h2_tags: string[]
    common_h3_tags: string[]
    keyword_frequency: Record<string, number>
    competitor_count: number
    competitors: CompetitorData[]
    generated_at: string
}

export interface SerpResponse {
    keyword: string
    market: string
    total_results: number
    results: SerpResult[]
    cached: boolean
    fetched_at: string
}

export const researchService = {
    /**
     * Get SERP results for a keyword
     */
    async getSerpResults(keyword: string, market: string = 'tw', numResults: number = 10): Promise<SerpResponse> {
        const response = await api.get<SerpResponse>('/research/serp', {
            params: { keyword, market, num_results: numResults }
        })
        return response.data
    },

    /**
     * Perform full keyword analysis (SERP + crawl + analysis)
     */
    async analyzeKeyword(keyword: string, market: string = 'tw', depth: number = 10): Promise<AnalysisReport> {
        const response = await api.get<AnalysisReport>('/research/analyze', {
            params: { keyword, market, depth }
        })
        return response.data
    },

    /**
     * Submit keyword for async research (returns task ID)
     */
    async submitResearch(keyword: string, market: string = 'tw', depth: number = 10): Promise<{ task_id: string }> {
        const response = await api.post('/research/keyword', {
            keyword,
            market,
            depth
        })
        return response.data
    },

    /**
     * Get research task status
     */
    async getTaskStatus(taskId: string): Promise<any> {
        const response = await api.get(`/research/${taskId}`)
        return response.data
    }
}
