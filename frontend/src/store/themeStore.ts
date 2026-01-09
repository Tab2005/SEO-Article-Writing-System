import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark'

interface ThemeState {
    theme: Theme
    setTheme: (theme: Theme) => void
    toggleTheme: () => void
    initTheme: () => void
}

export const useThemeStore = create<ThemeState>()(
    persist(
        (set, get) => ({
            theme: 'light',

            setTheme: (theme) => {
                const root = document.documentElement
                if (theme === 'dark') {
                    root.classList.add('dark')
                } else {
                    root.classList.remove('dark')
                }
                set({ theme })
            },

            toggleTheme: () => {
                const current = get().theme
                const next = current === 'dark' ? 'light' : 'dark'
                const root = document.documentElement

                if (next === 'dark') {
                    root.classList.add('dark')
                } else {
                    root.classList.remove('dark')
                }
                set({ theme: next })
            },

            initTheme: () => {
                const { theme } = get()
                const root = document.documentElement
                if (theme === 'dark') {
                    root.classList.add('dark')
                } else {
                    root.classList.remove('dark')
                }
            },
        }),
        {
            name: 'theme-storage',
        }
    )
)
