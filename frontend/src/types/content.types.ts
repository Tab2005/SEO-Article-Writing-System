export interface OutlineSection {
    heading: string
    level: number
    key_points: string[]
    subsections: OutlineSection[]
}

export interface ArticleOutline {
    title: string
    meta_description: string
    sections: OutlineSection[]
    estimated_word_count: number
    target_keywords: string[]
}

export interface Article {
    id: string
    project_id: string
    title: string
    slug?: string
    content?: string
    outline?: ArticleOutline
    target_keyword: string
    secondary_keywords?: string[]
    meta_description?: string
    word_count: number
    version: number
    status: 'draft' | 'generating' | 'review' | 'published' | 'archived'
    created_at: string
    updated_at: string
    published_at?: string
}
