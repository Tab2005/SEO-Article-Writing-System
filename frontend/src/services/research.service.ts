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

export interface TopicTheme {
    theme_name: string
    coverage_count: number
    total_competitors: number
    example_headings: string[]
}

// TF-IDF 關鍵詞分析相關介面
export interface KeywordItem {
    term: string
    score: number
}

export interface KeywordCount {
    term: string
    count: number
}

export interface KeywordCategories {
    high_frequency: KeywordItem[]
    semantic_related: KeywordItem[]
    long_tail: KeywordItem[]
}

export interface TFIDFAnalysis {
    suggested_keywords: KeywordItem[]
    keyword_categories: KeywordCategories
    competitor_common_terms: KeywordCount[]
}

export interface AnalysisReport {
    keyword: string
    market: string
    avg_word_count: number
    min_word_count: number
    max_word_count: number
    common_h2_tags: string[]
    common_h3_tags: string[]
    topic_themes?: TopicTheme[]
    keyword_frequency: Record<string, number>
    tfidf_analysis?: TFIDFAnalysis  // TF-IDF 關鍵詞分析
    competitor_count: number
    competitors: CompetitorData[]
    generated_at: string
}

export interface ResearchJob {
    job_id: string
    keyword: string
    market: string
    depth: number
    status: string
    progress: number
    message?: string
    error?: string
    created_at: string
    started_at?: string
    completed_at?: string
}

export interface ResearchCompetitorSummary {
    rank: number
    url: string
    serp_title?: string
    snippet?: string
    fetch_status: string
    http_status?: number
    error?: string
    page_title?: string
    meta_description?: string
    word_count?: number
    scraped_at?: string
    has_content: boolean
}

export interface ResearchCompetitorContent {
    rank: number
    url: string
    page_title?: string
    content_text: string
    scraped_at?: string
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
     * Create a persistent research job (async, stored in DB)
     */
    async createJob(keyword: string, market: string = 'tw', depth: number = 10): Promise<ResearchJob> {
        const response = await api.post<ResearchJob>('/research/jobs', {
            keyword,
            market,
            depth,
        })
        return response.data
    },

    /**
     * List all research jobs (history)
     */
    async listJobs(params?: { limit?: number; offset?: number; keyword?: string; status?: string }): Promise<ResearchJob[]> {
        const response = await api.get<ResearchJob[]>('/research/jobs', { params })
        return response.data
    },

    /**
     * Delete a research job
     */
    async deleteJob(jobId: string): Promise<void> {
        await api.delete(`/research/jobs/${jobId}`)
    },

    /**
     * Get persistent research job status
     */
    async getJob(jobId: string): Promise<ResearchJob> {
        const response = await api.get<ResearchJob>(`/research/jobs/${jobId}`)
        return response.data
    },

    /**
     * Get AnalysisReport generated for a job
     */
    async getJobReport(jobId: string): Promise<AnalysisReport> {
        const response = await api.get<AnalysisReport>(`/research/jobs/${jobId}/report`)
        return response.data
    },

    /**
     * List competitors for a job (no full text)
     */
    async listJobCompetitors(jobId: string): Promise<ResearchCompetitorSummary[]> {
        const response = await api.get<ResearchCompetitorSummary[]>(`/research/jobs/${jobId}/competitors`)
        return response.data
    },

    /**
     * Get single competitor full content text
     */
    async getJobCompetitorContent(jobId: string, rank: number): Promise<ResearchCompetitorContent> {
        const response = await api.get<ResearchCompetitorContent>(`/research/jobs/${jobId}/competitors/${rank}/content`)
        return response.data
    },

    /**
     * Get research task status
     */
    async getTaskStatus(taskId: string): Promise<any> {
        const response = await api.get(`/research/${taskId}`)
        return response.data
    },

    /**
     * Analyze topic themes from competitor headings (on-demand)
     */
    async analyzeTopicThemes(keyword: string, headings: string[][]): Promise<{ topic_themes: TopicTheme[], error?: string }> {
        const response = await api.post('/research/analyze-themes', {
            keyword,
            headings
        })
        return response.data
    }
}
