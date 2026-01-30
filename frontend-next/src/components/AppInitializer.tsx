'use client';

import { useEffect, useState } from 'react';
import { useStore, Note, NoteFolder } from '@/store/useStore';

// Mappers from NotesPage.tsx to keep consistency
const mapNoteFromApi = (note: any): Note => ({
    id: note.id,
    title: note.title,
    content: note.content,
    folder: note.folder_id,
    color: note.color,
    isPinned: note.pinned,
    tags: note.tags || [],
    createdAt: new Date(note.created_at),
    updatedAt: new Date(note.updated_at)
});

const mapFolderFromApi = (folder: any): NoteFolder => ({
    id: folder.id,
    name: folder.name,
    icon: folder.icon,
    parentId: folder.parent_id,
    color: folder.color,
    createdAt: new Date(folder.created_at)
});

export function AppInitializer() {
    const { setNotes, setFolders } = useStore();
    const [initialized, setInitialized] = useState(false);

    useEffect(() => {
        if (initialized) return;

        const syncWithBackend = async () => {
            try {
                const [notesRes, foldersRes] = await Promise.all([
                    fetch('/api/notes?include_subfolders=true'),
                    fetch('/api/folders/all')
                ]);

                if (notesRes.ok) {
                    const data = await notesRes.json();
                    setNotes(data.notes.map(mapNoteFromApi));
                }

                if (foldersRes.ok) {
                    const data = await foldersRes.json();
                    setFolders(data.folders.map(mapFolderFromApi));
                }

                setInitialized(true);
            } catch (error) {
                console.error('Backend sync failed:', error);
            }
        };

        syncWithBackend();
    }, [setNotes, setFolders, initialized]);

    return null;
}
