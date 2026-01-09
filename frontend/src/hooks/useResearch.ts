import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { researchService, AnalysisReport } from '../services/research.service'

/**
 * Hook for keyword analysis
 */
export function useKeywordAnalysis() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({ keyword, market, depth }: { keyword: string; market?: string; depth?: number }) =>
            researchService.analyzeKeyword(keyword, market, depth),
        onSuccess: (data, variables) => {
            // Cache the result
            queryClient.setQueryData(['research', variables.keyword, variables.market], data)
        },
    })
}

/**
 * Hook for getting cached analysis results
 */
export function useCachedAnalysis(keyword: string, market: string) {
    return useQuery<AnalysisReport>({
        queryKey: ['research', keyword, market],
        queryFn: () => researchService.analyzeKeyword(keyword, market),
        enabled: false, // Don't auto-fetch, use mutation instead
        staleTime: 5 * 60 * 1000, // 5 minutes
    })
}

/**
 * Hook for SERP results only
 */
export function useSerpResults(keyword: string, market: string) {
    return useQuery({
        queryKey: ['serp', keyword, market],
        queryFn: () => researchService.getSerpResults(keyword, market),
        enabled: !!keyword,
        staleTime: 5 * 60 * 1000,
    })
}
