'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from '@/components/layout/Sidebar';
import { ChatPage } from '@/components/pages/ChatPage';
import { DocumentsPage } from '@/components/pages/DocumentsPage';
import { HistoryPage } from '@/components/pages/HistoryPage';
import { DashboardPage } from '@/components/pages/DashboardPage';
import { SettingsPage } from '@/components/pages/SettingsPage';
import { NotesPage } from '@/components/pages/NotesPage';
import MindPage from '@/components/pages/MindPage';
import { LearningPage } from '@/components/pages/LearningPage';
import { FavoritesPage } from '@/components/pages/FavoritesPage';
import { TemplatesPage } from '@/components/pages/TemplatesPage';
import { SearchPage } from '@/components/pages/SearchPage';
import { KeyboardShortcutsModal } from '@/components/modals/KeyboardShortcutsModal';
import { CommandPalette } from '@/components/features/CommandPalette';
import { useStore } from '@/store/useStore';

export default function Home() {
  const { currentPage, setCurrentPage, theme, setTheme } = useStore();
  const [mounted, setMounted] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Global keyboard shortcuts
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Don't trigger shortcuts when typing in inputs
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
      return;
    }

    // Ctrl + ? - Show keyboard shortcuts
    if (e.ctrlKey && e.key === '?') {
      e.preventDefault();
      setShowShortcuts(true);
    }

    // Ctrl + K - Command Palette
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      setShowCommandPalette(true);
    }

    // Ctrl + P - Quick search (Spotlight)
    if (e.ctrlKey && e.key === 'p') {
      e.preventDefault();
      setCurrentPage('search');
    }

    // Ctrl + N - New chat
    if (e.ctrlKey && e.key === 'n') {
      e.preventDefault();
      setCurrentPage('chat');
    }

    // Ctrl + , - Settings
    if (e.ctrlKey && e.key === ',') {
      e.preventDefault();
      setCurrentPage('settings');
    }

    // Ctrl + Shift + T - Toggle theme
    if (e.ctrlKey && e.shiftKey && e.key === 'T') {
      e.preventDefault();
      setTheme(theme === 'light' ? 'dark' : 'light');
    }

    // Ctrl + 1-5 - Navigation shortcuts
    if (e.ctrlKey && !e.shiftKey && !e.altKey) {
      switch (e.key) {
        case '1':
          e.preventDefault();
          setCurrentPage('chat');
          break;
        case '2':
          e.preventDefault();
          setCurrentPage('history');
          break;
        case '3':
          e.preventDefault();
          setCurrentPage('notes');
          break;
        case '4':
          e.preventDefault();
          setCurrentPage('documents');
          break;
        case '5':
          e.preventDefault();
          setCurrentPage('learning');
          break;
      }
    }
  }, [setCurrentPage, theme, setTheme]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  if (!mounted) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
          <p className="text-muted-foreground">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'chat':
        return <ChatPage />;
      case 'documents':
        return <DocumentsPage />;
      case 'history':
        return <HistoryPage />;
      case 'dashboard':
        return <DashboardPage />;
      case 'settings':
        return <SettingsPage />;
      case 'notes':
        return <NotesPage />;
      case 'mind':
        return <MindPage />;
      case 'learning':
        return <LearningPage />;
      case 'favorites':
        return <FavoritesPage />;
      case 'templates':
        return <TemplatesPage />;
      case 'search':
        return <SearchPage />;
      default:
        return <ChatPage />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentPage}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="h-full"
          >
            {renderPage()}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Keyboard Shortcuts Modal */}
      <KeyboardShortcutsModal
        isOpen={showShortcuts}
        onClose={() => setShowShortcuts(false)}
      />

      {/* Command Palette */}
      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
      />
    </div>
  );
}
