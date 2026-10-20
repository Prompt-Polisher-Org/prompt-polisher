'use client';

/**
 * ThemeProvider.tsx — Dark / Light Mode System
 *
 * Reads from localStorage on first mount and applies the correct
 * data-theme attribute to <html>. Exposes a toggleTheme() function
 * via the useTheme() hook so any component can switch themes.
 *
 * Usage (root layout.tsx):
 *   <ThemeProvider>{children}</ThemeProvider>
 *
 * Usage (any component):
 *   const { theme, toggleTheme } = useTheme();
 */

import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'dark' | 'light';

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: 'dark',
  toggleTheme: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('dark');

  // On mount: read preference from localStorage (or system preference)
  useEffect(() => {
    const stored = window.localStorage.getItem('theme') as Theme | null;
    if (stored === 'light' || stored === 'dark') {
      setTheme(stored);
      document.documentElement.setAttribute('data-theme', stored);
    } else {
      // Fall back to system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const resolved: Theme = prefersDark ? 'dark' : 'light';
      setTheme(resolved);
      document.documentElement.setAttribute('data-theme', resolved);
    }
  }, []);

  const toggleTheme = () => {
    // Read the DOM value as well as React state so the control remains usable
    // during the first hydrated render, before the saved preference is loaded.
    const current = document.documentElement.getAttribute('data-theme') as Theme | null;
    const next: Theme = (current ?? theme) === 'dark' ? 'light' : 'dark';
    setTheme(next);
    window.localStorage.setItem('theme', next);
    document.documentElement.setAttribute('data-theme', next);
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}
