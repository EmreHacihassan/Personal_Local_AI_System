'use client';

import dynamic from 'next/dynamic';

// FloatingWidget'ı client-side only olarak yükle (SSR bypass)
const FloatingWidget = dynamic(
  () => import('./FloatingWidget').then(mod => mod.FloatingWidget),
  { ssr: false }
);

export function WidgetWrapper() {
  return <FloatingWidget />;
}
