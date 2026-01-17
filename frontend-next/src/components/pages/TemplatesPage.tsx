'use client';

import { motion } from 'framer-motion';
import { FileText, Plus, Edit, Trash2, Copy, Send, Search } from 'lucide-react';
import { useStore, Template } from '@/store/useStore';
import { cn } from '@/lib/utils';
import { useState, useMemo } from 'react';

const CATEGORIES = [
  { id: 'all', tr: 'Tümü', en: 'All', de: 'Alle', icon: '📋' },
  { id: 'work', tr: 'İş', en: 'Work', de: 'Arbeit', icon: '💼' },
  { id: 'coding', tr: 'Kodlama', en: 'Coding', de: 'Programmierung', icon: '💻' },
  { id: 'writing', tr: 'Yazı', en: 'Writing', de: 'Schreiben', icon: '✍️' },
  { id: 'research', tr: 'Araştırma', en: 'Research', de: 'Forschung', icon: '🔬' },
  { id: 'learning', tr: 'Öğrenme', en: 'Learning', de: 'Lernen', icon: '📚' },
  { id: 'creative', tr: 'Yaratıcı', en: 'Creative', de: 'Kreativ', icon: '🎨' },
  { id: 'other', tr: 'Diğer', en: 'Other', de: 'Sonstiges', icon: '📌' },
];

// Example templates for new users
const EXAMPLE_TEMPLATES = [
  {
    id: 'example-1',
    title: { tr: 'Kod Açıklama', en: 'Code Explanation', de: 'Code-Erklärung' },
    content: { 
      tr: 'Bu kodu satır satır açıkla ve ne yaptığını anlat:\n\n```\n{KODU BURAYA YAPIŞTIRIN}\n```',
      en: 'Explain this code line by line and describe what it does:\n\n```\n{PASTE CODE HERE}\n```',
      de: 'Erkläre diesen Code Zeile für Zeile und beschreibe, was er tut:\n\n```\n{CODE HIER EINFÜGEN}\n```'
    },
    category: 'coding',
  },
  {
    id: 'example-2',
    title: { tr: 'Profesyonel E-posta', en: 'Professional Email', de: 'Professionelle E-Mail' },
    content: {
      tr: 'Aşağıdaki konuda profesyonel bir e-posta yaz:\n\nKonu: {KONU}\nAlıcı: {ALICI}\nTon: Resmi\n\nAna mesaj: {MESAJ}',
      en: 'Write a professional email about the following:\n\nSubject: {SUBJECT}\nRecipient: {RECIPIENT}\nTone: Formal\n\nMain message: {MESSAGE}',
      de: 'Schreibe eine professionelle E-Mail zu folgendem Thema:\n\nBetreff: {BETREFF}\nEmpfänger: {EMPFÄNGER}\nTon: Formell\n\nHauptnachricht: {NACHRICHT}'
    },
    category: 'work',
  },
  {
    id: 'example-3',
    title: { tr: 'Makale Özeti', en: 'Article Summary', de: 'Artikelzusammenfassung' },
    content: {
      tr: 'Aşağıdaki metni özetle ve ana noktalarını çıkar:\n\n{METİN}\n\nLütfen şunları içersin:\n- Ana fikir\n- Kilit noktalar\n- Sonuç',
      en: 'Summarize the following text and extract the main points:\n\n{TEXT}\n\nPlease include:\n- Main idea\n- Key points\n- Conclusion',
      de: 'Fasse den folgenden Text zusammen und extrahiere die Hauptpunkte:\n\n{TEXT}\n\nBitte enthalte:\n- Hauptidee\n- Schlüsselpunkte\n- Fazit'
    },
    category: 'research',
  },
  {
    id: 'example-4',
    title: { tr: 'Öğrenme Rehberi', en: 'Learning Guide', de: 'Lernleitfaden' },
    content: {
      tr: '{KONU} hakkında başlangıçtan ileri seviyeye öğrenme planı oluştur.\n\nLütfen şunları içersin:\n- Ön bilgi gereksinimleri\n- Haftalık öğrenme planı\n- Önerilen kaynaklar\n- Pratik projeler',
      en: 'Create a learning plan from beginner to advanced about {TOPIC}.\n\nPlease include:\n- Prerequisites\n- Weekly learning plan\n- Recommended resources\n- Practice projects',
      de: 'Erstelle einen Lernplan von Anfänger bis Fortgeschritten über {THEMA}.\n\nBitte enthalte:\n- Voraussetzungen\n- Wöchentlicher Lernplan\n- Empfohlene Ressourcen\n- Übungsprojekte'
    },
    category: 'learning',
  },
  {
    id: 'example-5',
    title: { tr: 'Yaratıcı Hikaye', en: 'Creative Story', de: 'Kreative Geschichte' },
    content: {
      tr: 'Aşağıdaki özelliklere sahip kısa bir hikaye yaz:\n\nTür: {TÜR}\nAna karakter: {KARAKTER}\nMekan: {MEKAN}\nTema: {TEMA}\n\nYaklaşık 500 kelime olsun.',
      en: 'Write a short story with the following characteristics:\n\nGenre: {GENRE}\nMain character: {CHARACTER}\nSetting: {SETTING}\nTheme: {THEME}\n\nApproximately 500 words.',
      de: 'Schreibe eine Kurzgeschichte mit folgenden Merkmalen:\n\nGenre: {GENRE}\nHauptfigur: {CHARAKTER}\nSchauplatz: {SCHAUPLATZ}\nThema: {THEMA}\n\nUngefähr 500 Wörter.'
    },
    category: 'creative',
  },
];

export function TemplatesPage() {
  const { language, templates, addTemplate, updateTemplate, deleteTemplate, setCurrentPage } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({ title: '', content: '', category: 'work' });

  // Add example template
  const addExampleTemplate = (example: typeof EXAMPLE_TEMPLATES[0]) => {
    const newTemplate: Template = {
      id: Date.now().toString() + '-' + example.id,
      title: example.title[language],
      content: example.content[language],
      category: example.category,
      createdAt: new Date(),
      useCount: 0,
    };
    addTemplate(newTemplate);
  };

  const filteredTemplates = useMemo(() => {
    return templates
      .filter((t) => selectedCategory === 'all' || t.category === selectedCategory)
      .filter((t) => 
        searchQuery === '' || 
        t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.content.toLowerCase().includes(searchQuery.toLowerCase())
      );
  }, [templates, searchQuery, selectedCategory]);

  const handleCreate = () => {
    if (!formData.title.trim() || !formData.content.trim()) return;
    
    const newTemplate: Template = {
      id: Date.now().toString(),
      title: formData.title,
      content: formData.content,
      category: formData.category,
      createdAt: new Date(),
    };
    
    addTemplate(newTemplate);
    setFormData({ title: '', content: '', category: 'work' });
    setIsCreating(false);
  };

  const handleUpdate = () => {
    if (!editingId || !formData.title.trim() || !formData.content.trim()) return;
    
    updateTemplate(editingId, {
      title: formData.title,
      content: formData.content,
      category: formData.category,
    });
    
    setFormData({ title: '', content: '', category: 'work' });
    setEditingId(null);
  };

  const startEdit = (template: Template) => {
    setFormData({ 
      title: template.title, 
      content: template.content, 
      category: template.category 
    });
    setEditingId(template.id);
    setIsCreating(false);
  };

  const applyTemplate = (content: string) => {
    // Navigate to chat page - content will be pre-filled
    navigator.clipboard.writeText(content);
    setCurrentPage('chat');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const t = {
    title: { tr: 'Şablonlar', en: 'Templates', de: 'Vorlagen' },
    subtitle: { tr: 'Sık kullandığınız promptları kaydedin', en: 'Save your frequently used prompts', de: 'Speichern Sie häufig verwendete Prompts' },
    search: { tr: 'Şablonlarda ara...', en: 'Search templates...', de: 'Vorlagen durchsuchen...' },
    newTemplate: { tr: 'Yeni Şablon', en: 'New Template', de: 'Neue Vorlage' },
    templateTitle: { tr: 'Şablon Başlığı', en: 'Template Title', de: 'Vorlagetitel' },
    templateContent: { tr: 'Şablon İçeriği', en: 'Template Content', de: 'Vorlageinhalt' },
    category: { tr: 'Kategori', en: 'Category', de: 'Kategorie' },
    save: { tr: 'Kaydet', en: 'Save', de: 'Speichern' },
    cancel: { tr: 'İptal', en: 'Cancel', de: 'Abbrechen' },
    update: { tr: 'Güncelle', en: 'Update', de: 'Aktualisieren' },
    use: { tr: 'Kullan', en: 'Use', de: 'Verwenden' },
    copy: { tr: 'Kopyala', en: 'Copy', de: 'Kopieren' },
    edit: { tr: 'Düzenle', en: 'Edit', de: 'Bearbeiten' },
    delete: { tr: 'Sil', en: 'Delete', de: 'Löschen' },
    noTemplates: { tr: 'Henüz şablon yok', en: 'No templates yet', de: 'Noch keine Vorlagen' },
    noTemplatesHint: { 
      tr: 'Sık kullandığınız promptları şablon olarak kaydedin.', 
      en: 'Save your frequently used prompts as templates.', 
      de: 'Speichern Sie häufig verwendete Prompts als Vorlagen.' 
    },
    total: { tr: 'Toplam', en: 'Total', de: 'Gesamt' },
    templates: { tr: 'şablon', en: 'templates', de: 'Vorlagen' },
  };

  const getCategoryName = (catId: string) => {
    const cat = CATEGORIES.find(c => c.id === catId);
    if (!cat) return catId;
    return cat[language as 'tr' | 'en' | 'de'] || cat.en;
  };

  const getCategoryIcon = (catId: string) => {
    const cat = CATEGORIES.find(c => c.id === catId);
    return cat?.icon || '📋';
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 text-white">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">{t.title[language]}</h1>
            <p className="text-xs text-muted-foreground">{t.subtitle[language]}</p>
          </div>
        </div>
        <button
          onClick={() => {
            setIsCreating(true);
            setEditingId(null);
            setFormData({ title: '', content: '', category: 'work' });
          }}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
        >
          <Plus className="w-4 h-4" />
          {t.newTemplate[language]}
        </button>
      </header>

      {/* Search and Categories */}
      <div className="px-6 py-4 border-b border-border bg-muted/30 space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder={t.search[language]}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Categories */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-xl text-sm whitespace-nowrap transition-all",
                selectedCategory === cat.id 
                  ? "bg-primary-500 text-white" 
                  : "bg-background border border-border hover:bg-accent"
              )}
            >
              <span>{cat.icon}</span>
              <span>{cat[language as 'tr' | 'en' | 'de']}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Create/Edit Form */}
        {(isCreating || editingId) && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 bg-card border border-border rounded-2xl p-6"
          >
            <h3 className="text-lg font-semibold mb-4">
              {editingId ? t.edit[language] : t.newTemplate[language]}
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">{t.templateTitle[language]}</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder={language === 'tr' ? 'Örn: Kod İncelemesi' : 'e.g., Code Review'}
                  className="w-full px-4 py-2 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">{t.templateContent[language]}</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  placeholder={language === 'tr' ? 'Şablon içeriğinizi buraya yazın...' : 'Write your template content here...'}
                  rows={4}
                  className="w-full px-4 py-2 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">{t.category[language]}</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-4 py-2 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  {CATEGORIES.filter(c => c.id !== 'all').map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat[language as 'tr' | 'en' | 'de']}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="flex gap-3 pt-2">
                <button
                  onClick={editingId ? handleUpdate : handleCreate}
                  className="flex-1 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
                >
                  {editingId ? t.update[language] : t.save[language]}
                </button>
                <button
                  onClick={() => {
                    setIsCreating(false);
                    setEditingId(null);
                    setFormData({ title: '', content: '', category: 'work' });
                  }}
                  className="flex-1 py-2 bg-muted hover:bg-accent rounded-xl transition-colors"
                >
                  {t.cancel[language]}
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Templates List */}
        {filteredTemplates.length === 0 && !isCreating && !editingId ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center text-center py-12"
          >
            <div className="w-20 h-20 rounded-full bg-purple-100 dark:bg-purple-900/20 flex items-center justify-center mb-4">
              <FileText className="w-10 h-10 text-purple-500" />
            </div>
            <h3 className="text-lg font-semibold mb-2">{t.noTemplates[language]}</h3>
            <p className="text-sm text-muted-foreground max-w-md mb-6">
              {t.noTemplatesHint[language]}
            </p>
            
            {/* Example Templates Section */}
            <div className="w-full max-w-4xl">
              <h4 className="text-sm font-medium text-muted-foreground mb-4">
                {language === 'tr' ? '📋 Örnek Şablonlar' : language === 'de' ? '📋 Beispielvorlagen' : '📋 Example Templates'}
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {EXAMPLE_TEMPLATES.map((example) => (
                  <button
                    key={example.id}
                    onClick={() => addExampleTemplate(example)}
                    className="p-3 text-left bg-muted/50 hover:bg-muted border border-border rounded-xl transition-all group"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">{CATEGORIES.find(c => c.id === example.category)?.icon}</span>
                      <span className="font-medium text-sm">{example.title[language]}</span>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {example.content[language].substring(0, 80)}...
                    </p>
                    <span className="inline-flex items-center gap-1 mt-2 text-xs text-primary-500 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Plus className="w-3 h-3" />
                      {language === 'tr' ? 'Ekle' : language === 'de' ? 'Hinzufügen' : 'Add'}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTemplates.map((template, index) => (
              <motion.div
                key={template.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="bg-card border border-border rounded-2xl p-4 hover:shadow-md transition-shadow group"
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{getCategoryIcon(template.category)}</span>
                    <h4 className="font-semibold">{template.title}</h4>
                  </div>
                  <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-full">
                    {getCategoryName(template.category)}
                  </span>
                </div>

                {/* Content Preview */}
                <p className="text-sm text-muted-foreground mb-4 line-clamp-3">
                  {template.content}
                </p>

                {/* Actions */}
                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => applyTemplate(template.content)}
                    className="flex-1 flex items-center justify-center gap-1 py-2 bg-primary-500 text-white rounded-xl text-sm hover:bg-primary-600 transition-colors"
                  >
                    <Send className="w-3 h-3" />
                    {t.use[language]}
                  </button>
                  <button
                    onClick={() => copyToClipboard(template.content)}
                    className="p-2 bg-muted hover:bg-accent rounded-xl transition-colors"
                    title={t.copy[language]}
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => startEdit(template)}
                    className="p-2 bg-muted hover:bg-accent rounded-xl transition-colors"
                    title={t.edit[language]}
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => deleteTemplate(template.id)}
                    className="p-2 bg-muted hover:bg-red-100 dark:hover:bg-red-900/20 text-red-500 rounded-xl transition-colors"
                    title={t.delete[language]}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
