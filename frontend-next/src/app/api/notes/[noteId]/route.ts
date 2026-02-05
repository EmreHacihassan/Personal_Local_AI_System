/**
 * 📝 Single Note API Proxy
 * Proxies single note requests to the backend
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

        const backendUrl = `${BACKEND_URL}/api/notes/${noteId}`;
        console.log('[Note] Fetching from:', backendUrl);

        const response = await fetch(backendUrl, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: AbortSignal.timeout(15000),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[Note] Backend error:', response.status, errorText);
            return NextResponse.json(
                { detail: `Backend error: ${response.status}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('[Note] Error:', error);
        return NextResponse.json(
            { detail: error instanceof Error ? error.message : 'Bilinmeyen hata' },
            { status: 500 }
        );
    }
}

export async function PUT(
    request: NextRequest,
    { params }: { params: { noteId: string } }
) {
    try {
        const noteId = params.noteId;
        const body = await request.json();

        const backendUrl = `${BACKEND_URL}/api/notes/${noteId}`;
        console.log('[Note] Updating:', backendUrl);

        const response = await fetch(backendUrl, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
            signal: AbortSignal.timeout(15000),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[Note] Update error:', response.status, errorText);
            return NextResponse.json(
                { detail: `Backend error: ${response.status}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('[Note] Update error:', error);
        return NextResponse.json(
            { detail: error instanceof Error ? error.message : 'Bilinmeyen hata' },
            { status: 500 }
        );
    }
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: { noteId: string } }
) {
    try {
        const noteId = params.noteId;

        const backendUrl = `${BACKEND_URL}/api/notes/${noteId}`;
        console.log('[Note] Deleting:', backendUrl);

        const response = await fetch(backendUrl, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            signal: AbortSignal.timeout(15000),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[Note] Delete error:', response.status, errorText);
            return NextResponse.json(
                { detail: `Backend error: ${response.status}` },
                { status: response.status }
            );
        }

        return NextResponse.json({ success: true, message: 'Not silindi' });
    } catch (error) {
        console.error('[Note] Delete error:', error);
        return NextResponse.json(
            { detail: error instanceof Error ? error.message : 'Bilinmeyen hata' },
            { status: 500 }
        );
    }
}
