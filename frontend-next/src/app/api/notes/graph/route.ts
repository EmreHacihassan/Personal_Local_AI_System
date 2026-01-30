/**
 * 🧠 Notes Graph API Proxy
 * Proxies the Mind graph endpoint to the backend
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

export async function GET(request: NextRequest) {
    try {
        // Get query params
        const searchParams = request.nextUrl.searchParams;
        const params = new URLSearchParams();

        // Forward all query parameters
        searchParams.forEach((value, key) => {
            params.append(key, value);
        });

        // Make request to backend
        const backendUrl = `${BACKEND_URL}/api/notes/graph?${params.toString()}`;
        console.log('[Notes Graph] Fetching from:', backendUrl);

        const response = await fetch(backendUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            // Add timeout
            signal: AbortSignal.timeout(30000), // 30 second timeout
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[Notes Graph] Backend error:', response.status, errorText);
            return NextResponse.json(
                { detail: `Backend error: ${response.status}` },
                { status: response.status }
            );
        }

        const data = await response.json();

        // Log success
        console.log('[Notes Graph] Success:', {
            nodes: data.nodes?.length || 0,
            edges: data.edges?.length || 0
        });

        return NextResponse.json(data);
    } catch (error) {
        console.error('[Notes Graph] Error:', error);

        // Check if backend is down
        if (error instanceof TypeError && error.message.includes('fetch')) {
            return NextResponse.json(
                {
                    detail: 'Backend bağlantısı kurulamadı. Lütfen backend\'in çalıştığından emin olun.',
                    hint: 'Terminal\'de: python run.py'
                },
                { status: 503 }
            );
        }

        return NextResponse.json(
            { detail: error instanceof Error ? error.message : 'Bilinmeyen hata' },
            { status: 500 }
        );
    }
}
