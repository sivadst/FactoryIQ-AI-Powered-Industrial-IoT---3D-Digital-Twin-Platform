'use client'

import { useThemeStore } from '@/lib/theme'
import { Sun, Moon } from 'lucide-react'

export function ThemeToggle() {
  const theme = useThemeStore((state) => state.theme)
  const toggleTheme = useThemeStore((state) => state.toggleTheme)
  const isDark = theme === 'dark'

  return (
    <button
      id="theme-toggle"
      onClick={toggleTheme}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="relative flex items-center w-14 h-7 rounded-full transition-all duration-300 ease-in-out 
        bg-slate-200 dark:bg-slate-700 
        border border-slate-300 dark:border-slate-600
        hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500/40"
      aria-label="Toggle theme"
    >
      {/* Sun icon (left side - for light mode) */}
      <Sun className={`absolute left-1.5 w-3.5 h-3.5 transition-all duration-300 ${
        isDark ? 'text-slate-500 opacity-40' : 'text-amber-500 opacity-100'
      }`} />
      
      {/* Moon icon (right side - for dark mode) */}
      <Moon className={`absolute right-1.5 w-3.5 h-3.5 transition-all duration-300 ${
        isDark ? 'text-blue-300 opacity-100' : 'text-slate-400 opacity-40'
      }`} />

      {/* Slider Thumb */}
      <span
        className={`absolute top-0.5 w-6 h-6 rounded-full shadow-md transition-all duration-300 ease-in-out
          ${isDark 
            ? 'translate-x-[1.75rem] bg-slate-800 border border-slate-600' 
            : 'translate-x-0.5 bg-white border border-slate-200'
          }`}
      />
    </button>
  )
}
