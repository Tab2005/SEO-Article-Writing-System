import { useMutation } from '@tanstack/react-query'
import { contentService, OutlineRequest, ContentRequest } from '../services/content.service'

/**
 * Hook for generating article outline
 */
export function useGenerateOutline() {
    return useMutation({
        mutationFn: (request: OutlineRequest) => contentService.generateOutline(request),
    })
}

/**
 * Hook for generating full article content
 */
export function useGenerateContent() {
    return useMutation({
        mutationFn: (request: ContentRequest) => contentService.generateContent(request),
    })
}

/**
 * Hook for optimizing content
 */
export function useOptimizeContent() {
    return useMutation({
        mutationFn: ({ content, keywords }: { content: string; keywords: string[] }) =>
            contentService.optimizeContent(content, keywords),
    })
}
