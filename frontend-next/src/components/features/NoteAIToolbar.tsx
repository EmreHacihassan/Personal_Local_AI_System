'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Sparkles,
    Tag,
    Link2,
    FileText,
    Zap,
    Lightbulb,
    GraduationCap,
    MessageSquare,
    Loader2,
    Check,
    X,
    Copy,
    ChevronDown,
    ChevronUp,
    Brain
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface AIToolbarProps {
    noteId: string;
    noteTitle: string;
    noteContent: string;
    language: 'tr' | 'en' | 'de';
    onApplySuggestion?: (content: string) => void;
    onApplyTags?: (tags: string[]) => void;
}

interface FlashcardData {
    id: string;
    front: string;
    back: string;
    difficulty: string;
}

interface RelatedNoteData {
    note: {
        id: string;
        title: string;
        content: string;
    };
    similarity: number;
}

export function NoteAIToolbar({
    noteId,
    noteTitle,
    noteContent,
    language,
    onApplySuggestion,
    onApplyTags
}: AIToolbarProps) {
    // State for each feature
    const [isExpanded, setIsExpanded] = useState(false);
    const [activeFeature, setActiveFeature] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Results
    const [summary, setSummary] = useState<{ summary: string; key_points: string[] } | null>(null);
    const [suggestedTags, setSuggestedTags] = useState<string[]>([]);
    const [relatedNotes, setRelatedNotes] = useState<RelatedNoteData[]>([]);
    const [flashcards, setFlashcards] = useState<FlashcardData[]>([]);
    const [enrichedContent, setEnrichedContent] = useState<string | null>(null);
    const [qaAnswer, setQaAnswer] = useState<{ answer: string; confidence: number } | null>(null);
    const [question, setQuestion] = useState('');

    const t = {
        aiFeatures: { tr: 'AI Özellikleri', en: 'AI Features', de: 'KI-Funktionen' },
        summarize: { tr: 'Özetle', en: 'Summarize', de: 'Zusammenfassen' },
        suggestTags: { tr: 'Etiket Öner', en: 'Suggest Tags', de: 'Tags vorschlagen' },
        findRelated: { tr: 'İlgili Notlar', en: 'Related Notes', de: 'Ähnliche Notizen' },
        flashcards: { tr: 'Flashcard Oluştur', en: 'Create Flashcards', de: 'Karteikarten erstellen' },
        enrich: { tr: 'Zenginleştir', en: 'Enrich', de: 'Anreichern' },
        askQuestion: { tr: 'Soru Sor', en: 'Ask Question', de: 'Frage stellen' },
        apply: { tr: 'Uygula', en: 'Apply', de: 'Anwenden' },
        loading: { tr: 'Yükleniyor...', en: 'Loading...', de: 'Laden...' },
        error: { tr: 'Hata oluştu', en: 'An error occurred', de: 'Ein Fehler ist aufgetreten' },
        keyPoints: { tr: 'Önemli Noktalar', en: 'Key Points', de: 'Wichtige Punkte' },
        similarity: { tr: 'Benzerlik', en: 'Similarity', de: 'Ähnlichkeit' },
        front: { tr: 'Ön', en: 'Front', de: 'Vorderseite' },
        back: { tr: 'Arka', en: 'Back', de: 'Rückseite' },
        questionPlaceholder: { tr: 'Notunuz hakkında soru sorun...', en: 'Ask a question about your note...', de: 'Stellen Sie eine Frage zu Ihrer Notiz...' },
        ask: { tr: 'Sor', en: 'Ask', de: 'Fragen' },
        confidence: { tr: 'Güven', en: 'Confidence', de: 'Vertrauen' },
        close: { tr: 'Kapat', en: 'Close', de: 'Schließen' },
        copyToClipboard: { tr: 'Kopyala', en: 'Copy', de: 'Kopieren' },
        copied: { tr: 'Kopyalandı!', en: 'Copied!', de: 'Kopiert!' }
    };

    // API calls
    const handleSummarize = async () => {
        setActiveFeature('summarize');
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/notes/${noteId}/summarize`, { method: 'POST' });
            if (!response.ok) throw new Error('API error');
            const data = await response.json();
            setSummary(data);
        } catch {
            setError(t.error[language]);
        }
        setLoading(false);
    };

    const handleSuggestTags = async () => {
        setActiveFeature('tags');
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/notes/${noteId}/suggest-tags`, { method: 'POST' });
            if (!response.ok) throw new Error('API error');
            const data = await response.json();
            setSuggestedTags(data.tags || []);
        } catch {
            setError(t.error[language]);
        }
        setLoading(false);
    };

    const handleFindRelated = async () => {
        setActiveFeature('related');
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/notes/${noteId}/related`);
            if (!response.ok) throw new Error('API error');
            const data = await response.json();
            setRelatedNotes(data.related_notes || []);
        } catch {
            setError(t.error[language]);
        }
        setLoading(false);
    };

    const handleFlashcards = async () => {
        setActiveFeature('flashcards');
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/notes/${noteId}/flashcards`, { method: 'POST' });
            if (!response.ok) throw new Error('API error');
            const data = await response.json();
            setFlashcards(data.flashcards || []);
        } catch {
            setError(t.error[language]);
        }
        setLoading(false);
    };

    const handleEnrich = async () => {
        setActiveFeature('enrich');
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/notes/${noteId}/enrich`, { method: 'POST' });
            if (!response.ok) throw new Error('API error');
            const data = await response.json();
            setEnrichedContent(data.enriched_content || null);
        } catch {
            setError(t.error[language]);
        }
        setLoading(false);
    };

    const handleAskQuestion = async () => {
        if (!question.trim()) return;
        setActiveFeature('qa');
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/notes/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    note_ids: [noteId]
                })
            });
            if (!response.ok) throw new Error('API error');
            const data = await response.json();
            setQaAnswer({ answer: data.answer, confidence: data.confidence });
        } catch {
            setError(t.error[language]);
        }
        setLoading(false);
    };

    const handleApplyTags = () => {
        if (onApplyTags && suggestedTags.length > 0) {
            onApplyTags(suggestedTags);
        }
    };

    const handleApplyEnriched = () => {
        if (onApplySuggestion && enrichedContent) {
            onApplySuggestion(enrichedContent);
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    const features = [
        { id: 'summarize', icon: FileText, label: t.summarize[language], action: handleSummarize, color: 'from-blue-500 to-cyan-500' },
        { id: 'tags', icon: Tag, label: t.suggestTags[language], action: handleSuggestTags, color: 'from-green-500 to-emerald-500' },
        { id: 'related', icon: Link2, label: t.findRelated[language], action: handleFindRelated, color: 'from-purple-500 to-pink-500' },
        { id: 'flashcards', icon: GraduationCap, label: t.flashcards[language], action: handleFlashcards, color: 'from-orange-500 to-amber-500' },
        { id: 'enrich', icon: Lightbulb, label: t.enrich[language], action: handleEnrich, color: 'from-violet-500 to-purple-500' },
    ];

    return (
        <div className="border-t border-border bg-gradient-to-r from-purple-500/5 via-pink-500/5 to-blue-500/5">
            {/* Toggle Button */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors"
            >
                <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500">
                        <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <span className="font-medium text-sm">{t.aiFeatures[language]}</span>
                    <span className="px-2 py-0.5 rounded-full text-xs bg-purple-500/20 text-purple-600 dark:text-purple-400">
                        Beta
                    </span>
                </div>
                {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-muted-foreground" />
                ) : (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                )}
            </button>

            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        <div className="px-4 pb-4 space-y-4">
                            {/* Feature Buttons */}
                            <div className="flex flex-wrap gap-2">
                                {features.map((feature) => {
                                    const Icon = feature.icon;
                                    const isActive = activeFeature === feature.id;

                                    return (
                                        <motion.button
                                            key={feature.id}
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={feature.action}
                                            disabled={loading}
                                            className={cn(
                                                "flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all",
                                                isActive
                                                    ? `bg-gradient-to-r ${feature.color} text-white shadow-lg`
                                                    : "bg-white/10 hover:bg-white/20 text-foreground"
                                            )}
                                        >
                                            {loading && isActive ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                <Icon className="w-4 h-4" />
                                            )}
                                            {feature.label}
                                        </motion.button>
                                    );
                                })}
                            </div>

                            {/* Q&A Input */}
                            <div className="flex gap-2">
                                <div className="relative flex-1">
                                    <MessageSquare className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                    <input
                                        type="text"
                                        value={question}
                                        onChange={(e) => setQuestion(e.target.value)}
                                        placeholder={t.questionPlaceholder[language]}
                                        className="w-full pl-10 pr-4 py-2 rounded-xl bg-white/10 border border-white/10 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                                        onKeyDown={(e) => e.key === 'Enter' && handleAskQuestion()}
                                    />
                                </div>
                                <button
                                    onClick={handleAskQuestion}
                                    disabled={!question.trim() || loading}
                                    className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium disabled:opacity-50 transition-all"
                                >
                                    {loading && activeFeature === 'qa' ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        t.ask[language]
                                    )}
                                </button>
                            </div>

                            {/* Error */}
                            {error && (
                                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-sm">
                                    {error}
                                </div>
                            )}

                            {/* Results */}
                            <AnimatePresence mode="wait">
                                {/* Summary Result */}
                                {activeFeature === 'summarize' && summary && !loading && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3"
                                    >
                                        <div className="flex items-center justify-between">
                                            <h4 className="font-medium text-sm flex items-center gap-2">
                                                <FileText className="w-4 h-4 text-blue-500" />
                                                {t.summarize[language]}
                                            </h4>
                                            <button
                                                onClick={() => copyToClipboard(summary.summary)}
                                                className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                                                title={t.copyToClipboard[language]}
                                            >
                                                <Copy className="w-4 h-4" />
                                            </button>
                                        </div>
                                        <p className="text-sm text-muted-foreground">{summary.summary}</p>
                                        {summary.key_points && summary.key_points.length > 0 && (
                                            <div>
                                                <h5 className="text-xs font-medium text-muted-foreground mb-2">{t.keyPoints[language]}:</h5>
                                                <ul className="space-y-1">
                                                    {summary.key_points.map((point, i) => (
                                                        <li key={i} className="text-sm flex items-start gap-2">
                                                            <Check className="w-3 h-3 text-green-500 mt-1 flex-shrink-0" />
                                                            {point}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </motion.div>
                                )}

                                {/* Tags Result */}
                                {activeFeature === 'tags' && suggestedTags.length > 0 && !loading && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3"
                                    >
                                        <h4 className="font-medium text-sm flex items-center gap-2">
                                            <Tag className="w-4 h-4 text-green-500" />
                                            {t.suggestTags[language]}
                                        </h4>
                                        <div className="flex flex-wrap gap-2">
                                            {suggestedTags.map((tag, i) => (
                                                <span
                                                    key={i}
                                                    className="px-3 py-1 rounded-full text-sm bg-green-500/20 text-green-600 dark:text-green-400"
                                                >
                                                    #{tag}
                                                </span>
                                            ))}
                                        </div>
                                        {onApplyTags && (
                                            <button
                                                onClick={handleApplyTags}
                                                className="w-full py-2 rounded-lg bg-green-500/20 text-green-600 dark:text-green-400 text-sm font-medium hover:bg-green-500/30 transition-colors"
                                            >
                                                {t.apply[language]}
                                            </button>
                                        )}
                                    </motion.div>
                                )}

                                {/* Related Notes Result */}
                                {activeFeature === 'related' && relatedNotes.length > 0 && !loading && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3"
                                    >
                                        <h4 className="font-medium text-sm flex items-center gap-2">
                                            <Link2 className="w-4 h-4 text-purple-500" />
                                            {t.findRelated[language]}
                                        </h4>
                                        <div className="space-y-2">
                                            {relatedNotes.map((item, i) => (
                                                <div
                                                    key={i}
                                                    className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors cursor-pointer"
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <span className="font-medium text-sm">{item.note.title}</span>
                                                        <span className="text-xs text-purple-500">
                                                            {t.similarity[language]}: {Math.round(item.similarity * 100)}%
                                                        </span>
                                                    </div>
                                                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                                        {item.note.content?.substring(0, 100)}...
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                    </motion.div>
                                )}

                                {/* Flashcards Result */}
                                {activeFeature === 'flashcards' && flashcards.length > 0 && !loading && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3"
                                    >
                                        <h4 className="font-medium text-sm flex items-center gap-2">
                                            <GraduationCap className="w-4 h-4 text-orange-500" />
                                            {t.flashcards[language]} ({flashcards.length})
                                        </h4>
                                        <div className="space-y-3">
                                            {flashcards.map((card, i) => (
                                                <div key={card.id} className="p-3 rounded-lg bg-white/5 space-y-2">
                                                    <div>
                                                        <span className="text-xs text-orange-500 font-medium">{t.front[language]}:</span>
                                                        <p className="text-sm">{card.front}</p>
                                                    </div>
                                                    <div>
                                                        <span className="text-xs text-green-500 font-medium">{t.back[language]}:</span>
                                                        <p className="text-sm text-muted-foreground">{card.back}</p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </motion.div>
                                )}

                                {/* Enriched Content Result */}
                                {activeFeature === 'enrich' && enrichedContent && !loading && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3"
                                    >
                                        <h4 className="font-medium text-sm flex items-center gap-2">
                                            <Lightbulb className="w-4 h-4 text-violet-500" />
                                            {t.enrich[language]}
                                        </h4>
                                        <div className="prose prose-sm dark:prose-invert max-h-60 overflow-y-auto">
                                            <p className="text-sm whitespace-pre-wrap">{enrichedContent}</p>
                                        </div>
                                        {onApplySuggestion && (
                                            <button
                                                onClick={handleApplyEnriched}
                                                className="w-full py-2 rounded-lg bg-violet-500/20 text-violet-600 dark:text-violet-400 text-sm font-medium hover:bg-violet-500/30 transition-colors"
                                            >
                                                {t.apply[language]}
                                            </button>
                                        )}
                                    </motion.div>
                                )}

                                {/* Q&A Result */}
                                {activeFeature === 'qa' && qaAnswer && !loading && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3"
                                    >
                                        <h4 className="font-medium text-sm flex items-center gap-2">
                                            <Brain className="w-4 h-4 text-pink-500" />
                                            {t.askQuestion[language]}
                                        </h4>
                                        <p className="text-sm">{qaAnswer.answer}</p>
                                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                            <span>{t.confidence[language]}:</span>
                                            <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-pink-500 to-purple-500 rounded-full"
                                                    style={{ width: `${qaAnswer.confidence * 100}%` }}
                                                />
                                            </div>
                                            <span>{Math.round(qaAnswer.confidence * 100)}%</span>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

export default NoteAIToolbar;
