/**
 * 📝 Notes API Proxy
 * Proxies all notes endpoints to the backend
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

// GET /api/notes - List all notes
export async function GET(request: NextRequest) {
    try {
        const searchParams = request.nextUrl.searchParams;
        const params = new URLSearchParams();

        searchParams.forEach((value, key) => {
            params.append(key, value);
        });

        const backendUrl = `${BACKEND_URL}/api/notes?${params.toString()}`;

        const response = await fetch(backendUrl, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: AbortSignal.timeout(15000),
        });

        if (!response.ok) {
            return NextResponse.json(
                { detail: `Backend error: ${response.status}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('[Notes API] GET Error:', error);
        return NextResponse.json(
            { detail: error instanceof Error ? error.message : 'Hata' },
            { status: 500 }
        );
    }
}

// POST /api/notes - Create note
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        const response = await fetch(`${BACKEND_URL}/api/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
            signal: AbortSignal.timeout(15000),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            return NextResponse.json(
                { detail: errorData.detail || `Backend error: ${response.status}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data, { status: 201 });
    } catch (error) {
        console.error('[Notes API] POST Error:', error);
        return NextResponse.json(
            { detail: error instanceof Error ? error.message : 'Hata' },
            { status: 500 }
        );
    }
}
