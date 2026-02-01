import { useState, useEffect, useCallback } from 'react';

interface NoteVersion {
    id: string;
    note_id: string;
    title: string;
    content: string;
    tags: string[];
    created_at: string;
    change_summary: string;
}

interface VersionDiff {
    title_changed: boolean;
    content_diff: {
        added_lines: string[];
        removed_lines: string[];
        added_count: number;
        removed_count: number;
    };
    tags_diff: {
        added: string[];
        removed: string[];
    };
}

interface UseNoteVersionsReturn {
    versions: NoteVersion[];
    isLoading: boolean;
    error: string | null;
    fetchVersions: () => Promise<void>;
    restoreVersion: (versionId: string) => Promise<boolean>;
    getDiff: (versionId1: string, versionId2: string) => Promise<VersionDiff | null>;
}

export function useNoteVersions(noteId: string | null): UseNoteVersionsReturn {
    const [versions, setVersions] = useState<NoteVersion[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchVersions = useCallback(async () => {
        if (!noteId) return;
        
        setIsLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`http://localhost:8001/api/notes/${noteId}/versions`);
            if (!response.ok) {
                throw new Error('Versiyonlar yüklenemedi');
            }
            const data = await response.json();
            setVersions(data.versions || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Bir hata oluştu');
            console.error('Fetch versions error:', err);
        } finally {
            setIsLoading(false);
        }
    }, [noteId]);

    const restoreVersion = useCallback(async (versionId: string): Promise<boolean> => {
        if (!noteId) return false;
        
        try {
            const response = await fetch(`http://localhost:8001/api/notes/${noteId}/restore/${versionId}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Geri yükleme başarısız');
            }
            
            // Refresh versions after restore
            await fetchVersions();
            return true;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Geri yükleme hatası');
            console.error('Restore version error:', err);
            return false;
        }
    }, [noteId, fetchVersions]);

    const getDiff = useCallback(async (versionId1: string, versionId2: string): Promise<VersionDiff | null> => {
        if (!noteId) return null;
        
        try {
            const response = await fetch(`http://localhost:8001/api/notes/${noteId}/diff/${versionId1}/${versionId2}`);
            
            if (!response.ok) {
                throw new Error('Diff alınamadı');
            }
            
            const data = await response.json();
            return data.diff;
        } catch (err) {
            console.error('Get diff error:', err);
            return null;
        }
    }, [noteId]);

    // Fetch versions when noteId changes
    useEffect(() => {
        if (noteId) {
            fetchVersions();
        } else {
            setVersions([]);
        }
    }, [noteId, fetchVersions]);

    return {
        versions,
        isLoading,
        error,
        fetchVersions,
        restoreVersion,
        getDiff
    };
}

export type { NoteVersion, VersionDiff };
