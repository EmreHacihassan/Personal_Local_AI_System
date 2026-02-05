/**
 * 🔗 Graph Clusters API Proxy
 * Proxies cluster requests to the backend
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

export async function GET(request: NextRequest) {
    try {
        const backendUrl = `${BACKEND_URL}/api/notes/graph/clusters`;
        console.log('[Clusters] Fetching from:', backendUrl);

        const response = await fetch(backendUrl, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: AbortSignal.timeout(15000),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[Clusters] Backend error:', response.status, errorText);
            return NextResponse.json(
                { detail: `Backend error: ${response.status}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        console.log('[Clusters] Success:', data.clusters?.length || 0, 'clusters');

        return NextResponse.json(data);
    } catch (error) {
        console.error('[Clusters] Error:', error);
        return NextResponse.json(
            { clusters: [], detail: error instanceof Error ? error.message : 'Bilinmeyen hata' },
            { status: 500 }
        );
    }
}
