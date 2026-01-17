'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageSquare, 
  FileText, 
  History, 
  LayoutDashboard, 
  Settings, 
  StickyNote,
  GraduationCap,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Menu
} from 'lucide-react';
import { useStore, Page } from '@/store/useStore';
import { cn } from '@/lib/utils';

const menuItems: { id: Page; icon: React.ElementType; label: string; labelEn: string }[] = [
  { id: 'chat', icon: MessageSquare, label: 'Sohbet', labelEn: 'Chat' },
  { id: 'documents', icon: FileText, label: 'Dökümanlar', labelEn: 'Documents' },
  { id: 'history', icon: History, label: 'Geçmiş', labelEn: 'History' },
  { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard', labelEn: 'Dashboard' },
  { id: 'notes', icon: StickyNote, label: 'Notlar', labelEn: 'Notes' },
  { id: 'learning', icon: GraduationCap, label: 'AI ile Öğren', labelEn: 'Learn with AI' },
  { id: 'settings', icon: Settings, label: 'Ayarlar', labelEn: 'Settings' },
];

export function Sidebar() {
  const { 
    currentPage, 
    setCurrentPage, 
    sidebarCollapsed, 
    toggleSidebar,
    language 
  } = useStore();

  return (
    <motion.aside
      initial={false}
      animate={{ width: sidebarCollapsed ? 72 : 260 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className={cn(
        "flex flex-col h-full bg-card border-r border-border",
        "relative z-20"
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-border">
        <motion.div 
          className="flex items-center gap-3"
          animate={{ justifyContent: sidebarCollapsed ? 'center' : 'flex-start' }}
        >
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 text-white">
            <Sparkles className="w-5 h-5" />
          </div>
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
              >
                <h1 className="text-lg font-bold gradient-text whitespace-nowrap">
                  Enterprise AI
                </h1>
                <p className="text-xs text-muted-foreground">v2.0</p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          
          return (
            <motion.button
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200",
                "hover:bg-accent group relative",
                isActive && "bg-primary-500/10 text-primary-600 dark:text-primary-400"
              )}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {/* Active indicator */}
              {isActive && (
                <motion.div
                  layoutId="activeIndicator"
                  className="absolute left-0 w-1 h-8 bg-primary-500 rounded-r-full"
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              )}
              
              <Icon className={cn(
                "w-5 h-5 flex-shrink-0 transition-colors",
                isActive ? "text-primary-500" : "text-muted-foreground group-hover:text-foreground"
              )} />
              
              <AnimatePresence>
                {!sidebarCollapsed && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.2 }}
                    className={cn(
                      "text-sm font-medium whitespace-nowrap",
                      isActive ? "text-primary-600 dark:text-primary-400" : "text-foreground"
                    )}
                  >
                    {language === 'tr' ? item.label : item.labelEn}
                  </motion.span>
                )}
              </AnimatePresence>

              {/* Tooltip for collapsed state */}
              {sidebarCollapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-sm rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                  {language === 'tr' ? item.label : item.labelEn}
                </div>
              )}
            </motion.button>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-3 border-t border-border">
        <button
          onClick={toggleSidebar}
          className={cn(
            "w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl",
            "bg-muted hover:bg-accent transition-colors"
          )}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <>
              <ChevronLeft className="w-5 h-5" />
              <span className="text-sm">Daralt</span>
            </>
          )}
        </button>
      </div>
    </motion.aside>
  );
}
