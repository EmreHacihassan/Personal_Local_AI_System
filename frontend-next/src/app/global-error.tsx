'use client';

import { useEffect, useState } from 'react';

type Language = 'tr' | 'en' | 'de';

const translations = {
  tr: {
    title: '⚠️ Kritik Hata',
    description: 'Uygulama yüklenirken bir hata oluştu.',
    retry: 'Tekrar Dene',
    reload: 'Sayfayı Yenile',
    home: 'Ana Sayfa',
    errorCode: 'Hata Kodu',
    contactSupport: 'Sorun devam ederse lütfen sistem yöneticinize başvurun.',
  },
  en: {
    title: '⚠️ Critical Error',
    description: 'An error occurred while loading the application.',
    retry: 'Try Again',
    reload: 'Reload Page',
    home: 'Home',
    errorCode: 'Error Code',
    contactSupport: 'If the problem persists, please contact your system administrator.',
  },
  de: {
    title: '⚠️ Kritischer Fehler',
    description: 'Beim Laden der Anwendung ist ein Fehler aufgetreten.',
    retry: 'Erneut versuchen',
    reload: 'Seite neu laden',
    home: 'Startseite',
    errorCode: 'Fehlercode',
    contactSupport: 'Wenn das Problem weiterhin besteht, wenden Sie sich bitte an Ihren Systemadministrator.',
  },
};

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const [lang, setLang] = useState<Language>('tr');
  
  useEffect(() => {
    // Try to get language from localStorage
    const stored = localStorage.getItem('language');
    if (stored === 'en' || stored === 'de' || stored === 'tr') {
      setLang(stored);
    }
  }, []);
  
  const t = translations[lang];
  
  return (
    <html lang={lang}>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{t.title}</title>
      </head>
      <body style={{ margin: 0, fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif' }}>
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #1f2937 0%, #111827 100%)',
          padding: '1rem'
        }}>
          <div style={{
            maxWidth: '28rem',
            width: '100%',
            backgroundColor: 'rgba(55, 65, 81, 0.8)',
            backdropFilter: 'blur(10px)',
            borderRadius: '1.5rem',
            padding: '2.5rem',
            textAlign: 'center',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            {/* Error Icon */}
            <div style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(249, 115, 22, 0.2) 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.5rem',
              fontSize: '2.5rem'
            }}>
              ⚠️
            </div>
            
            <h1 style={{ 
              color: '#f87171', 
              fontSize: '1.75rem', 
              marginBottom: '1rem',
              fontWeight: 700,
              letterSpacing: '-0.025em'
            }}>
              {t.title.replace('⚠️ ', '')}
            </h1>
            
            <p style={{ 
              color: '#9ca3af', 
              marginBottom: '1.5rem',
              lineHeight: 1.6,
              fontSize: '1rem'
            }}>
              {t.description}
            </p>
            
            {/* Error Code */}
            {error.digest && (
              <div style={{
                backgroundColor: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '0.5rem',
                padding: '0.75rem',
                marginBottom: '1.5rem',
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                color: '#6b7280'
              }}>
                {t.errorCode}: <code style={{ color: '#f87171' }}>{error.digest}</code>
              </div>
            )}
            
            {/* Action Buttons */}
            <div style={{ 
              display: 'flex', 
              gap: '0.75rem', 
              justifyContent: 'center',
              flexWrap: 'wrap'
            }}>
              <button
                onClick={reset}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.75rem',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  boxShadow: '0 10px 15px -3px rgba(59, 130, 246, 0.3)',
                  transition: 'all 0.2s'
                }}
                onMouseOver={e => (e.currentTarget.style.transform = 'scale(1.05)')}
                onMouseOut={e => (e.currentTarget.style.transform = 'scale(1)')}
              >
                🔄 {t.retry}
              </button>
              
              <button
                onClick={() => window.location.reload()}
                style={{
                  padding: '0.75rem 1.5rem',
                  backgroundColor: 'rgba(75, 85, 99, 0.8)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.75rem',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  transition: 'all 0.2s'
                }}
                onMouseOver={e => (e.currentTarget.style.backgroundColor = 'rgba(75, 85, 99, 1)')}
                onMouseOut={e => (e.currentTarget.style.backgroundColor = 'rgba(75, 85, 99, 0.8)')}
              >
                {t.reload}
              </button>
              
              <button
                onClick={() => window.location.href = '/'}
                style={{
                  padding: '0.75rem 1.5rem',
                  backgroundColor: 'rgba(75, 85, 99, 0.8)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.75rem',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  transition: 'all 0.2s'
                }}
                onMouseOver={e => (e.currentTarget.style.backgroundColor = 'rgba(75, 85, 99, 1)')}
                onMouseOut={e => (e.currentTarget.style.backgroundColor = 'rgba(75, 85, 99, 0.8)')}
              >
                🏠 {t.home}
              </button>
            </div>
            
            {/* Support Text */}
            <p style={{
              marginTop: '2rem',
              fontSize: '0.75rem',
              color: '#6b7280'
            }}>
              {t.contactSupport}
            </p>
          </div>
        </div>
      </body>
    </html>
  );
}
