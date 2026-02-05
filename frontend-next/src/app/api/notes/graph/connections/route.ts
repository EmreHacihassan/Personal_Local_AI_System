/**
 * 🔗 Graph Connections API Proxy
 * Proxies connection count requests to the backend
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

export async function GET(request: NextRequest) {
    try {
        const backendUrl = `${BACKEND_URL}/api/notes/graph/connections`;
        console.log('[Connections] Fetching from:', backendUrl);

        const response = await fetch(backendUrl, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: AbortSignal.timeout(15000),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[Connections] Backend error:', response.status, errorText);
            return NextResponse.json(
                { detail: `Backend error: ${response.status}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        console.log('[Connections] Success:', Object.keys(data.connections || {}).length, 'nodes');

        return NextResponse.json(data);
    } catch (error) {
        console.error('[Connections] Error:', error);
        return NextResponse.json(
            { connections: {}, detail: error instanceof Error ? error.message : 'Bilinmeyen hata' },
            { status: 500 }
        );
    }
}
