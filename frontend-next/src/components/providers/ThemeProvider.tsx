'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { useStore } from '@/store/useStore';

type ThemeProviderProps = {
  children: React.ReactNode;
};

const ThemeContext = createContext<{ theme: string }>({ theme: 'light' });

export function ThemeProvider({ children }: ThemeProviderProps) {
  const { theme } = useStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted) {
      const root = document.documentElement;
      
      // Remove all theme classes
      root.classList.remove('light', 'dark');
      
      // Add appropriate class based on theme
      if (theme === 'dark' || theme === 'sunset') {
        root.classList.add('dark');
      } else {
        root.classList.add('light');
      }

      // Set theme-specific CSS variables
      const themes: Record<string, Record<string, string>> = {
        light: {
          '--theme-primary': '231 69% 63%',
          '--theme-secondary': '263 47% 58%',
        },
        dark: {
          '--theme-primary': '239 84% 67%',
          '--theme-secondary': '270 91% 65%',
        },
        ocean: {
          '--theme-primary': '199 89% 48%',
          '--theme-secondary': '217 91% 60%',
        },
        forest: {
          '--theme-primary': '160 84% 39%',
          '--theme-secondary': '158 64% 37%',
        },
        sunset: {
          '--theme-primary': '24 95% 53%',
          '--theme-secondary': '330 81% 60%',
        },
      };

      const themeVars = themes[theme] || themes.light;
      Object.entries(themeVars).forEach(([key, value]) => {
        root.style.setProperty(key, value);
      });
    }
  }, [theme, mounted]);

  // Show children immediately but with default light theme until hydrated
  return (
    <ThemeContext.Provider value={{ theme: mounted ? theme : 'light' }}>
      <div className={mounted ? '' : 'opacity-0'} style={{ transition: 'opacity 0.2s' }}>
        {children}
      </div>
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
