/**
 * 🛤️ Graph Path API Proxy
 * Proxies path-finding requests between two notes to the backend
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

export async function GET(request: NextRequest) {
    try {
        const searchParams = request.nextUrl.searchParams;
        const sourceId = searchParams.get('source_id');
        const targetId = searchParams.get('target_id');

        if (!sourceId || !targetId) {
            return NextResponse.json(
                { detail: 'source_id and target_id are required' },
                { status: 400 }
            );
        }

        const backendUrl = `${BACKEND_URL}/api/notes/graph/path?source_id=${sourceId}&target_id=${targetId}`;
        console.log('[Path] Finding path from', sourceId, 'to', targetId);

        const response = await fetch(backendUrl, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: AbortSignal.timeout(15000),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[Path] Backend error:', response.status, errorText);
            return NextResponse.json(
                { detail: `Backend error: ${response.status}`, path: [] },
                { status: response.status }
            );
        }

        const data = await response.json();
        console.log('[Path] Found path with', data.path?.length || 0, 'nodes');

        return NextResponse.json(data);
    } catch (error) {
        console.error('[Path] Error:', error);
        return NextResponse.json(
            { path: [], detail: error instanceof Error ? error.message : 'Bilinmeyen hata' },
            { status: 500 }
        );
    }
}
