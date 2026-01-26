import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/components/providers/ThemeProvider';
import { Toaster } from '@/components/ui/Toaster';
import { WidgetWrapper } from '@/components/widget/WidgetWrapper';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import dynamic from 'next/dynamic';

// Lazy load heavy components for performance
const VisionPanel = dynamic(() => import('@/components/ui/VisionPanel'), { ssr: false });
const ComputerUsePanel = dynamic(() => import('@/components/ui/ComputerUsePanel'), { ssr: false });

// Inter font with Latin Extended subset for Turkish characters (ğ, ü, ş, ı, ö, ç)
const inter = Inter({ 
  subsets: ['latin', 'latin-ext'],
  display: 'swap',
  variable: '--font-inter',
});

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0f172a' },
  ],
};

export const metadata: Metadata = {
  title: 'Enterprise AI Assistant',
  description: 'Endüstri Standartlarında Kurumsal AI Çözümü',
  icons: {
    icon: [
      { url: '/icon.svg', type: 'image/svg+xml' },
    ],
    apple: '/icon.svg',
  },
  // Charset is automatically set by Next.js, but we ensure it's UTF-8
  other: {
    'content-type': 'text/html; charset=utf-8',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr" suppressHydrationWarning>
      <head>
        {/* Explicit charset declaration for Turkish character support */}
        <meta charSet="utf-8" />
      </head>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider>
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
          <Toaster />
          <WidgetWrapper />
          {/* Premium AI Features - Floating Panels */}
          <VisionPanel />
          <ComputerUsePanel />
        </ThemeProvider>
      </body>
    </html>
  );
}
