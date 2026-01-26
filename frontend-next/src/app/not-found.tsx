'use client';

import Link from 'next/link';
import { Home, ArrowLeft, Compass } from 'lucide-react';
import { useEffect, useState } from 'react';
import { type Language } from '@/lib/i18n';

const translations = {
  tr: {
    title: 'Sayfa Bulunamadı',
    description: 'Aradığınız sayfa mevcut değil veya taşınmış olabilir.',
    home: 'Ana Sayfa',
    back: 'Geri Dön',
    search: 'Arama Yap',
  },
  en: {
    title: 'Page Not Found',
    description: 'The page you are looking for does not exist or may have been moved.',
    home: 'Home',
    back: 'Go Back',
    search: 'Search',
  },
  de: {
    title: 'Seite nicht gefunden',
    description: 'Die gesuchte Seite existiert nicht oder wurde verschoben.',
    home: 'Startseite',
    back: 'Zurück',
    search: 'Suchen',
  },
};

export default function NotFound() {
  const [lang, setLang] = useState<Language>('tr');
  
  useEffect(() => {
    const stored = localStorage.getItem('language');
    if (stored === 'en' || stored === 'de' || stored === 'tr') {
      setLang(stored);
    }
  }, []);
  
  const t = translations[lang];
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <div className="max-w-md w-full text-center">
        {/* Animated 404 */}
        <div className="relative mb-8">
          <div className="text-[10rem] font-black text-transparent bg-clip-text bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 leading-none select-none">
            404
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center animate-pulse">
              <Compass className="w-12 h-12 text-blue-500 animate-spin" style={{ animationDuration: '3s' }} />
            </div>
          </div>
        </div>
        
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
          {t.title}
        </h1>
        
        <p className="text-gray-600 dark:text-gray-400 mb-8 leading-relaxed">
          {t.description}
        </p>
        
        <div className="flex gap-3 justify-center flex-wrap">
          <Link
            href="/"
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:from-blue-600 hover:to-blue-700 transition-all shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:scale-105"
          >
            <Home className="w-4 h-4" />
            {t.home}
          </Link>
          
          <button
            onClick={() => window.history.back()}
            className="flex items-center gap-2 px-5 py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-300 dark:hover:bg-gray-600 transition-all hover:scale-105"
          >
            <ArrowLeft className="w-4 h-4" />
            {t.back}
          </button>
        </div>
      </div>
    </div>
  );
}
