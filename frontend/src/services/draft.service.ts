import api from './api'

export interface DraftCreateRequest {
    project_id: string
    keyword: string
    title?: string
    wizard_step?: number
    strategy_config?: Record<string, unknown>
    outline?: Record<string, unknown>
    research_job_id?: string
    brief_id?: string
}

export interface DraftUpdateRequest {
    title?: string
    wizard_step?: number
    strategy_config?: Record<string, unknown>
    outline?: Record<string, unknown>
    content?: string
    word_count?: number
    secondary_keywords?: string[]
    status?: string
    brief_id?: string
    qa_status?: string
    qa_results?: Record<string, unknown>
}

export interface Draft {
    id: string
    project_id: string
    title: string
    target_keyword: string
    wizard_step: number | null
    status: string
    strategy_config: Record<string, unknown> | null
    outline: Record<string, unknown> | null
    content: string | null
    word_count: number
    research_job_id: string | null
    secondary_keywords: string[] | null
    brief_id?: string | null
    qa_status?: string | null
    qa_results?: Record<string, unknown> | null
    created_at: string
    updated_at: string
}

export interface DraftListResponse {
    drafts: Draft[]
    count: number
}

// Streaming types
export interface StreamRequest {
    title: string
    target_keyword: string
    outline: Record<string, unknown>
    secondary_keywords?: string[]
    tone?: string
    draft_id?: string
}

export interface StreamProgressEvent {
    section: string
    current?: number
    total?: number
    progress: number
}

export interface StreamContentEvent {
    section: string
    content: string
    words?: number
}

export interface StreamDoneEvent {
    total_words: number
    total_sections?: number
    content: string
}

export const draftService = {
    /**
     * Create a new draft
     */
    async createDraft(request: DraftCreateRequest): Promise<Draft> {
        const response = await api.post<Draft>('/content/draft', request)
        return response.data
    },

    /**
     * Get a draft by ID
     */
    async getDraft(draftId: string): Promise<Draft> {
        const response = await api.get<Draft>(`/content/draft/${draftId}`)
        return response.data
    },

    /**
     * Update a draft
     */
    async updateDraft(draftId: string, request: DraftUpdateRequest): Promise<Draft> {
        const response = await api.patch<Draft>(`/content/draft/${draftId}`, request)
        return response.data
    },

    /**
     * Delete a draft
     */
    async deleteDraft(draftId: string): Promise<void> {
        await api.delete(`/content/draft/${draftId}`)
    },

    /**
     * List drafts
     */
    async listDrafts(params?: {
        project_id?: string
        status?: string
        limit?: number
        offset?: number
    }): Promise<DraftListResponse> {
        const response = await api.get<DraftListResponse>('/content/drafts', { params })
        return response.data
    },
}

export const streamingService = {
    /**
     * Start streaming content generation
     * 
     * Returns an EventSource for receiving SSE events
     */
    createEventSource(request: StreamRequest): {
        eventSource: EventSource | null
        startStreaming: (
            onProgress: (event: StreamProgressEvent) => void,
            onContent: (event: StreamContentEvent) => void,
            onDone: (event: StreamDoneEvent) => void,
            onError: (error: Error) => void
        ) => Promise<void>
    } {
        // For SSE via POST, we need to use fetch with ReadableStream
        // EventSource only supports GET requests

        return {
            eventSource: null,
            startStreaming: async (onProgress, onContent, onDone, onError) => {
                try {
                    const response = await fetch('/api/v1/content/generate-stream', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'text/event-stream',
                        },
                        body: JSON.stringify(request),
                    })

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`)
                    }

                    const reader = response.body?.getReader()
                    if (!reader) {
                        throw new Error('No response body')
                    }

                    const decoder = new TextDecoder()
                    let buffer = ''

                    while (true) {
                        const { done, value } = await reader.read()
                        if (done) break

                        buffer += decoder.decode(value, { stream: true })

                        // Parse SSE events from buffer
                        const events = buffer.split('\n\n')
                        buffer = events.pop() || '' // Keep incomplete event in buffer

                        for (const eventStr of events) {
                            if (!eventStr.trim()) continue

                            const lines = eventStr.split('\n')
                            let eventType = ''
                            let eventData = ''

                            for (const line of lines) {
                                if (line.startsWith('event: ')) {
                                    eventType = line.slice(7)
                                } else if (line.startsWith('data: ')) {
                                    eventData = line.slice(6)
                                }
                            }

                            if (eventType && eventData) {
                                try {
                                    const data = JSON.parse(eventData)
                                    switch (eventType) {
                                        case 'progress':
                                            onProgress(data as StreamProgressEvent)
                                            break
                                        case 'content':
                                            onContent(data as StreamContentEvent)
                                            break
                                        case 'done':
                                            onDone(data as StreamDoneEvent)
                                            break
                                    }
                                } catch (parseError) {
                                    console.error('Failed to parse SSE data:', parseError)
                                }
                            }
                        }
                    }
                } catch (error) {
                    onError(error instanceof Error ? error : new Error(String(error)))
                }
            },
        }
    },
}
