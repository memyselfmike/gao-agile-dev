/**
 * Theme Provider - System preference detection and theme management
 *
 * Features:
 * - Detects system preference via prefers-color-scheme
 * - Stores theme in localStorage (key: gao-dev-theme)
 * - Syncs theme across tabs via localStorage events
 * - No flash of unstyled content (FOUC)
 */
import { ThemeProvider as NextThemesProvider } from 'next-themes';
import type { ThemeProviderProps as NextThemesProviderProps } from 'next-themes';

type ThemeProviderProps = NextThemesProviderProps;

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem={true}
      storageKey="gao-dev-theme"
      disableTransitionOnChange={false}
      {...props}
    >
      {children}
    </NextThemesProvider>
  );
}
