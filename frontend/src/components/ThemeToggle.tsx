import { useEffect } from 'react'
import { Moon, Sun } from 'lucide-react'
import { useThemeStore } from '../store/themeStore'

export function ThemeToggle() {
    const { theme, toggleTheme, initTheme } = useThemeStore()

    // Initialize theme on mount
    useEffect(() => {
        initTheme()
    }, [])

    const handleToggle = () => {
        toggleTheme()
        // Force re-render by getting fresh state
        const newTheme = useThemeStore.getState().theme
        console.log('Theme toggled to:', newTheme)
        console.log('HTML classList:', document.documentElement.classList.toString())
    }

    return (
        <button
            onClick={handleToggle}
            className="p-2 rounded-lg transition-colors
                 text-gray-500 hover:text-gray-700 hover:bg-gray-100
                 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-slate-700"
            title={theme === 'dark' ? '切換為亮色模式' : '切換為暗色模式'}
        >
            {theme === 'dark' ? (
                <Sun className="w-5 h-5" />
            ) : (
                <Moon className="w-5 h-5" />
            )}
        </button>
    )
}
