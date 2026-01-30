'use client';

/**
 * TemplateSelector - Not Şablonları Seçici
 * 
 * Hazır şablonlar ve özel şablon oluşturma.
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Layout,
    Calendar,
    Users,
    Lightbulb,
    BookOpen,
    Target,
    Code,
    FileText,
    Plus,
    X,
    Check,
    Sparkles
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NoteTemplate {
    id: string;
    name: string;
    nameEn: string;
    icon: React.ReactNode;
    color: string;
    content: string;
    category: 'work' | 'personal' | 'study' | 'creative';
}

interface TemplateSelectorProps {
    onSelect: (content: string, title: string) => void;
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

const TEMPLATES: NoteTemplate[] = [
    {
        id: 'meeting',
        name: 'Toplantı Notu',
        nameEn: 'Meeting Notes',
        icon: <Users className="w-5 h-5" />,
        color: 'from-blue-500 to-cyan-500',
        category: 'work',
        content: `# Toplantı Notu

📅 **Tarih:** ${new Date().toLocaleDateString('tr-TR')}
👥 **Katılımcılar:** 

---

## 📋 Gündem
1. 
2. 
3. 

## 📝 Notlar


## ✅ Aksiyonlar
- [ ] 
- [ ] 
- [ ] 

## 📆 Sonraki Toplantı
**Tarih:** 
**Gündem:** `
    },
    {
        id: 'daily',
        name: 'Günlük',
        nameEn: 'Daily Journal',
        icon: <Calendar className="w-5 h-5" />,
        color: 'from-amber-500 to-orange-500',
        category: 'personal',
        content: `# 📔 ${new Date().toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}

## 🌅 Sabah Düşünceleri


## 📋 Bugünkü Görevler
- [ ] 
- [ ] 
- [ ] 

## 💡 Öğrendiklerim


## 🙏 Minnettarlık
- 
- 

## 🌙 Gün Sonu Değerlendirmesi
`
    },
    {
        id: 'project',
        name: 'Proje Planı',
        nameEn: 'Project Plan',
        icon: <Target className="w-5 h-5" />,
        color: 'from-purple-500 to-pink-500',
        category: 'work',
        content: `# 🎯 Proje: [Proje Adı]

## 📋 Özet
**Başlangıç:** ${new Date().toLocaleDateString('tr-TR')}
**Bitiş:** 
**Durum:** 🟡 Devam Ediyor

---

## 🎯 Hedefler
1. 
2. 
3. 

## 📊 Kilometre Taşları

| Aşama | Tarih | Durum |
|-------|-------|-------|
| Planlama | | ⏳ |
| Geliştirme | | ⏳ |
| Test | | ⏳ |
| Yayın | | ⏳ |

## 📁 Kaynaklar
- 

## ⚠️ Riskler
- 

## 📝 Notlar
`
    },
    {
        id: 'lecture',
        name: 'Ders Notu',
        nameEn: 'Lecture Notes',
        icon: <BookOpen className="w-5 h-5" />,
        color: 'from-emerald-500 to-teal-500',
        category: 'study',
        content: `# 📚 Ders: [Konu]

📅 **Tarih:** ${new Date().toLocaleDateString('tr-TR')}
👨‍🏫 **Eğitmen:** 

---

## 📝 Ana Kavramlar

### 1. 


### 2. 


### 3. 


## 💡 Önemli Noktalar
> 

## ❓ Sorular
- 

## 🔗 Kaynaklar
- 

## 📖 Ödev / İleri Okuma
- [ ] 
`
    },
    {
        id: 'idea',
        name: 'Fikir',
        nameEn: 'Idea',
        icon: <Lightbulb className="w-5 h-5" />,
        color: 'from-yellow-500 to-amber-500',
        category: 'creative',
        content: `# 💡 Fikir: [Başlık]

## 🎯 Özet
Kısa açıklama...

## 🤔 Problem
Hangi sorunu çözüyor?

## ✨ Çözüm
Nasıl çözüyor?

## 🎯 Hedef Kitle
Kimler için?

## 🔥 Önemli Çünkü...


## 📋 Sonraki Adımlar
- [ ] 
- [ ] 

## 🔗 İlgili Notlar
- [[]]
`
    },
    {
        id: 'code',
        name: 'Kod Notu',
        nameEn: 'Code Snippet',
        icon: <Code className="w-5 h-5" />,
        color: 'from-slate-600 to-zinc-700',
        category: 'work',
        content: `# 💻 [Konu/Teknoloji]

## 📝 Açıklama


## 🔧 Kod

\`\`\`javascript
// Kodunuz buraya
\`\`\`

## 📖 Kullanım


## ⚠️ Notlar
- 

## 🔗 Referanslar
- 
`
    },
    {
        id: 'research',
        name: 'Araştırma',
        nameEn: 'Research',
        icon: <FileText className="w-5 h-5" />,
        color: 'from-indigo-500 to-violet-500',
        category: 'study',
        content: `# 🔬 Araştırma: [Konu]

## 📋 Amaç
Bu araştırmanın amacı...

## 🔍 Sorular
1. 
2. 
3. 

## 📚 Kaynaklar
### Kitaplar
- 

### Makaleler
- 

### Web
- 

## 📝 Bulgular


## 💡 Sonuçlar


## 🔗 İlgili Konular
- [[]]
`
    },
    {
        id: 'blank',
        name: 'Boş Sayfa',
        nameEn: 'Blank Page',
        icon: <Plus className="w-5 h-5" />,
        color: 'from-gray-400 to-gray-500',
        category: 'personal',
        content: `# 

`
    }
];

const CATEGORIES = {
    work: { name: 'İş', nameEn: 'Work', icon: '💼' },
    personal: { name: 'Kişisel', nameEn: 'Personal', icon: '🏠' },
    study: { name: 'Eğitim', nameEn: 'Study', icon: '📚' },
    creative: { name: 'Yaratıcı', nameEn: 'Creative', icon: '🎨' },
};

const translations = {
    title: { tr: 'Şablon Seç', en: 'Choose Template', de: 'Vorlage wählen' },
    categories: { tr: 'Kategoriler', en: 'Categories', de: 'Kategorien' },
    all: { tr: 'Tümü', en: 'All', de: 'Alle' },
    useTemplate: { tr: 'Kullan', en: 'Use', de: 'Verwenden' },
};

export function TemplateSelector({ onSelect, onClose, language = 'tr' }: TemplateSelectorProps) {
    const t = translations;
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [hoveredTemplate, setHoveredTemplate] = useState<string | null>(null);

    const filteredTemplates = selectedCategory
        ? TEMPLATES.filter(t => t.category === selectedCategory)
        : TEMPLATES;

    const handleSelect = (template: NoteTemplate) => {
        const title = language === 'tr' ? template.name : template.nameEn;
        onSelect(template.content, title);
        onClose();
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
            onClick={onClose}
        >
            <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="w-full max-w-3xl max-h-[80vh] bg-card rounded-2xl shadow-2xl border border-border overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="p-4 border-b border-border bg-gradient-to-r from-primary-500/10 to-purple-500/10">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary-500 to-purple-500">
                                <Sparkles className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h2 className="font-semibold text-lg">{t.title[language]}</h2>
                                <p className="text-xs text-muted-foreground">
                                    {TEMPLATES.length} şablon
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-lg hover:bg-muted transition-colors"
                        >
                            <X className="w-5 h-5 text-muted-foreground" />
                        </button>
                    </div>

                    {/* Category Filters */}
                    <div className="flex items-center gap-2 overflow-x-auto pb-1">
                        <button
                            onClick={() => setSelectedCategory(null)}
                            className={cn(
                                "px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors",
                                !selectedCategory
                                    ? "bg-primary-500 text-white"
                                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                            )}
                        >
                            {t.all[language]}
                        </button>
                        {Object.entries(CATEGORIES).map(([key, cat]) => (
                            <button
                                key={key}
                                onClick={() => setSelectedCategory(key)}
                                className={cn(
                                    "px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors flex items-center gap-1.5",
                                    selectedCategory === key
                                        ? "bg-primary-500 text-white"
                                        : "bg-muted text-muted-foreground hover:bg-muted/80"
                                )}
                            >
                                <span>{cat.icon}</span>
                                {language === 'tr' ? cat.name : cat.nameEn}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Templates Grid */}
                <div className="p-4 overflow-y-auto max-h-[60vh]">
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        <AnimatePresence mode="popLayout">
                            {filteredTemplates.map((template, index) => (
                                <motion.button
                                    key={template.id}
                                    layout
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1, transition: { delay: index * 0.03 } }}
                                    exit={{ opacity: 0, scale: 0.9 }}
                                    whileHover={{ scale: 1.02, y: -2 }}
                                    whileTap={{ scale: 0.98 }}
                                    onMouseEnter={() => setHoveredTemplate(template.id)}
                                    onMouseLeave={() => setHoveredTemplate(null)}
                                    onClick={() => handleSelect(template)}
                                    className="relative p-4 rounded-xl border border-border hover:border-primary-500/50 transition-all text-left group overflow-hidden"
                                >
                                    {/* Background Gradient */}
                                    <div className={cn(
                                        "absolute inset-0 opacity-5 group-hover:opacity-10 transition-opacity bg-gradient-to-br",
                                        template.color
                                    )} />

                                    {/* Content */}
                                    <div className="relative">
                                        <div className={cn(
                                            "w-10 h-10 rounded-xl flex items-center justify-center mb-3 bg-gradient-to-br text-white",
                                            template.color
                                        )}>
                                            {template.icon}
                                        </div>
                                        <h4 className="font-medium text-sm mb-1">
                                            {language === 'tr' ? template.name : template.nameEn}
                                        </h4>
                                        <p className="text-[10px] text-muted-foreground line-clamp-2">
                                            {template.content.split('\n').slice(0, 2).join(' ').slice(0, 50)}...
                                        </p>
                                    </div>

                                    {/* Hover Indicator */}
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{
                                            opacity: hoveredTemplate === template.id ? 1 : 0,
                                            y: hoveredTemplate === template.id ? 0 : 10
                                        }}
                                        className="absolute bottom-2 right-2 px-2 py-1 rounded-md bg-primary-500 text-white text-[10px] font-medium flex items-center gap-1"
                                    >
                                        <Check className="w-3 h-3" />
                                        {t.useTemplate[language]}
                                    </motion.div>
                                </motion.button>
                            ))}
                        </AnimatePresence>
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
}

export default TemplateSelector;
