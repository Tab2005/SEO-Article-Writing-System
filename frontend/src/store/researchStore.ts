import { create } from 'zustand'
import { AnalysisReport } from '../services/research.service'

interface ResearchState {
    // Current research
    currentKeyword: string
    currentMarket: string
    currentReport: AnalysisReport | null

    // History
    recentSearches: { keyword: string; market: string; date: string }[]

    // Actions
    setCurrentResearch: (keyword: string, market: string, report: AnalysisReport) => void
    clearCurrentResearch: () => void
    addToHistory: (keyword: string, market: string) => void
}

export const useResearchStore = create<ResearchState>((set, get) => ({
    currentKeyword: '',
    currentMarket: 'tw',
    currentReport: null,
    recentSearches: [],

    setCurrentResearch: (keyword, market, report) =>
        set({
            currentKeyword: keyword,
            currentMarket: market,
            currentReport: report,
        }),

    clearCurrentResearch: () =>
        set({
            currentKeyword: '',
            currentMarket: 'tw',
            currentReport: null,
        }),

    addToHistory: (keyword, market) => {
        const { recentSearches } = get()
        const newSearch = {
            keyword,
            market,
            date: new Date().toISOString(),
        }

        // Keep only last 10 searches, avoid duplicates
        const filtered = recentSearches.filter(
            (s) => !(s.keyword === keyword && s.market === market)
        )

        set({
            recentSearches: [newSearch, ...filtered].slice(0, 10),
        })
    },
}))
