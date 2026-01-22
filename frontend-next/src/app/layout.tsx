import type { Metadata } from 'next';
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

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Enterprise AI Assistant',
  description: 'Endüstri Standartlarında Kurumsal AI Çözümü',
  icons: {
    icon: [
      { url: '/icon.svg', type: 'image/svg+xml' },
    ],
    apple: '/icon.svg',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr" suppressHydrationWarning>
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
