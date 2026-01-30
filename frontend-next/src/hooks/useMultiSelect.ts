'use client';

/**
 * useMultiSelect - Çoklu Seçim Hook'u
 * 
 * Ctrl+click ve Shift+click ile çoklu seçim işlevselliği.
 */

import { useState, useCallback, useMemo } from 'react';

interface UseMultiSelectOptions<T> {
    items: T[];
    getItemId: (item: T) => string;
}

interface UseMultiSelectReturn<T> {
    selectedIds: Set<string>;
    isSelected: (id: string) => boolean;
    toggle: (id: string, isCtrl?: boolean, isShift?: boolean) => void;
    selectAll: () => void;
    clearSelection: () => void;
    selectRange: (fromId: string, toId: string) => void;
    selectedItems: T[];
    hasSelection: boolean;
    selectionCount: number;
}

export function useMultiSelect<T>({ items, getItemId }: UseMultiSelectOptions<T>): UseMultiSelectReturn<T> {
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [lastSelectedId, setLastSelectedId] = useState<string | null>(null);

    const isSelected = useCallback((id: string) => selectedIds.has(id), [selectedIds]);

    const toggle = useCallback((id: string, isCtrl = false, isShift = false) => {
        setSelectedIds(prev => {
            const next = new Set(prev);

            if (isShift && lastSelectedId) {
                // Shift+click: select range
                const itemIds = items.map(getItemId);
                const fromIndex = itemIds.indexOf(lastSelectedId);
                const toIndex = itemIds.indexOf(id);

                if (fromIndex !== -1 && toIndex !== -1) {
                    const start = Math.min(fromIndex, toIndex);
                    const end = Math.max(fromIndex, toIndex);

                    for (let i = start; i <= end; i++) {
                        next.add(itemIds[i]);
                    }
                }
            } else if (isCtrl) {
                // Ctrl+click: toggle single
                if (next.has(id)) {
                    next.delete(id);
                } else {
                    next.add(id);
                }
            } else {
                // Normal click: select only this
                next.clear();
                next.add(id);
            }

            return next;
        });

        setLastSelectedId(id);
    }, [items, getItemId, lastSelectedId]);

    const selectAll = useCallback(() => {
        setSelectedIds(new Set(items.map(getItemId)));
    }, [items, getItemId]);

    const clearSelection = useCallback(() => {
        setSelectedIds(new Set());
        setLastSelectedId(null);
    }, []);

    const selectRange = useCallback((fromId: string, toId: string) => {
        const itemIds = items.map(getItemId);
        const fromIndex = itemIds.indexOf(fromId);
        const toIndex = itemIds.indexOf(toId);

        if (fromIndex !== -1 && toIndex !== -1) {
            const start = Math.min(fromIndex, toIndex);
            const end = Math.max(fromIndex, toIndex);

            setSelectedIds(new Set(itemIds.slice(start, end + 1)));
        }
    }, [items, getItemId]);

    const selectedItems = useMemo(() => {
        return items.filter(item => selectedIds.has(getItemId(item)));
    }, [items, selectedIds, getItemId]);

    const hasSelection = selectedIds.size > 0;
    const selectionCount = selectedIds.size;

    return {
        selectedIds,
        isSelected,
        toggle,
        selectAll,
        clearSelection,
        selectRange,
        selectedItems,
        hasSelection,
        selectionCount,
    };
}

export default useMultiSelect;
