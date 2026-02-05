/**
 * 🤖 Note AI Summary API Proxy
 * Proxies AI summary requests to the backend
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

export async function GET(
    request: NextRequest,
    { params }: { params: { noteId: string } }
) {
    try {
        const noteId = params.noteId;
        
        if (!noteId) {
            return NextResponse.json(
                { detail: 'Note ID is required' },
                { status: 400 }
            );
        }

        // Make request to backend
        const backendUrl = `${BACKEND_URL}/api/notes/${noteId}/ai-summary`;
        console.log('[AI Summary] Fetching from:', backendUrl);

        const response = await fetch(backendUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            signal: AbortSignal.timeout(30000), // AI processing may take longer
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[AI Summary] Backend error:', response.status, errorText);
            return NextResponse.json(
                { detail: `Backend error: ${response.status}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        console.log('[AI Summary] Success for note:', noteId);

        return NextResponse.json(data);
    } catch (error) {
        console.error('[AI Summary] Error:', error);

        if (error instanceof TypeError && error.message.includes('fetch')) {
            return NextResponse.json(
                { detail: 'Backend bağlantısı kurulamadı.' },
                { status: 503 }
            );
        }

        return NextResponse.json(
            { detail: error instanceof Error ? error.message : 'Bilinmeyen hata' },
            { status: 500 }
        );
    }
}
