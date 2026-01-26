'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug, Copy, Check } from 'lucide-react';
import { t, type Language } from '@/lib/i18n';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const [lang, setLang] = useState<Language>('tr');
  const [copied, setCopied] = useState(false);
  
  useEffect(() => {
    console.error('Application error:', error);
    // Get language from localStorage
    const stored = localStorage.getItem('language');
    if (stored === 'en' || stored === 'de' || stored === 'tr') {
      setLang(stored);
    }
  }, [error]);

  const handleCopyError = () => {
    const errorText = `Error: ${error.message}\n\nDigest: ${error.digest || 'N/A'}\n\nStack: ${error.stack || 'N/A'}`;
    navigator.clipboard.writeText(errorText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <div className="max-w-md w-full bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl rounded-2xl shadow-2xl p-8 text-center border border-gray-200/50 dark:border-gray-700/50">
        {/* Error Icon */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="p-4 bg-gradient-to-br from-red-100 to-orange-100 dark:from-red-900/30 dark:to-orange-900/30 rounded-full animate-pulse">
              <AlertTriangle className="w-12 h-12 text-red-500" />
            </div>
            <div className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
              <Bug className="w-3 h-3 text-white" />
            </div>
          </div>
        </div>
        
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
          {t('errorOccurred', lang)}
        </h1>
        
        <p className="text-gray-600 dark:text-gray-400 mb-6 leading-relaxed">
          {t('unexpectedError', lang)}
        </p>
        
        {/* Error Code */}
        {error.digest && (
          <div className="flex items-center justify-center gap-2 mb-6">
            <span className="text-xs text-gray-400 font-mono bg-gray-100 dark:bg-gray-700 px-3 py-1.5 rounded-lg">
              {t('errorDetails', lang).split(' ')[0]}: {error.digest}
            </span>
            <button
              onClick={handleCopyError}
              className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title={t('copyToClipboard', lang)}
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-500" />
              ) : (
                <Copy className="w-4 h-4 text-gray-400" />
              )}
            </button>
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="flex gap-3 justify-center flex-wrap">
          <button
            onClick={reset}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:from-blue-600 hover:to-blue-700 transition-all shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:scale-105"
          >
            <RefreshCw className="w-4 h-4" />
            {t('retry', lang)}
          </button>
          
          <button
            onClick={() => window.location.reload()}
            className="flex items-center gap-2 px-5 py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-300 dark:hover:bg-gray-600 transition-all hover:scale-105"
          >
            <RefreshCw className="w-4 h-4" />
            {t('reloadPage', lang)}
          </button>
          
          <a
            href="/"
            className="flex items-center gap-2 px-5 py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-300 dark:hover:bg-gray-600 transition-all hover:scale-105"
          >
            <Home className="w-4 h-4" />
            {t('goHome', lang)}
          </a>
        </div>
        
        {/* Support Text */}
        <p className="text-xs text-gray-400 mt-8">
          {lang === 'tr' && 'Sorun devam ederse lütfen sistem yöneticinize başvurun.'}
          {lang === 'en' && 'If the problem persists, please contact your system administrator.'}
          {lang === 'de' && 'Wenn das Problem weiterhin besteht, wenden Sie sich bitte an Ihren Systemadministrator.'}
        </p>
      </div>
    </div>
  );
}
