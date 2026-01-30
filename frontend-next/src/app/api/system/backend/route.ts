import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Project root path (assuming this runs in .next/server/app/api/...)
// We need to write to the project root where run.py can see it.
// In dev: process.cwd() is usually the project root (frontend-next or parent?)
// run.py is in parent of frontend-next.
const SIGNAL_FILE = path.join(process.cwd(), '..', '.backend_state');

export async function POST(req: Request) {
    try {
        const body = await req.json();
        const { action } = body;

        if (!['start', 'stop', 'restart'].includes(action)) {
            return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
        }

        // Write signal to file
        // stop -> "stopped"
        // start -> "running"
        // restart -> "restarting" (run.py will see this, kill, then set to "running")

        let state = 'running';
        if (action === 'stop') state = 'stopped';
        if (action === 'restart') state = 'restarting';

        fs.writeFileSync(SIGNAL_FILE, state, 'utf-8');

        return NextResponse.json({ success: true, state });
    } catch (error) {
        console.error('Backend control error:', error);
        return NextResponse.json({ error: 'Internal error' }, { status: 500 });
    }
}

export async function GET() {
    try {
        if (fs.existsSync(SIGNAL_FILE)) {
            const state = fs.readFileSync(SIGNAL_FILE, 'utf-8');
            return NextResponse.json({ state });
        }
        return NextResponse.json({ state: 'running' }); // Default
    } catch (error) {
        return NextResponse.json({ state: 'unknown' });
    }
}
