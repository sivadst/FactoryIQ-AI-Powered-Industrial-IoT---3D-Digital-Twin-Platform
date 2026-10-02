'use client'

import { create } from 'zustand'

type Theme = 'light' | 'dark'

interface ThemeStore {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

export const useThemeStore = create<ThemeStore>((set, get) => ({
  theme: 'light', // default to light mode
  setTheme: (theme) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('factoryiq-theme', theme)
    }
    set({ theme })
  },
  toggleTheme: () => {
    const current = get().theme
    const next = current === 'dark' ? 'light' : 'dark'
    if (typeof window !== 'undefined') {
      localStorage.setItem('factoryiq-theme', next)
    }
    set({ theme: next })
  },
}))

// Initialize theme from localStorage on load
export function initializeTheme() {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('factoryiq-theme') as Theme | null
    if (stored) {
      useThemeStore.getState().setTheme(stored)
    }
  }
}
