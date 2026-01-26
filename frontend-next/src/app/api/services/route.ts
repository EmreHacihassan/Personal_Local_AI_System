/**
 * 🚀 Local Service Starter API
 * This API route allows starting backend services directly from the frontend
 * when the main backend is not running.
 */

import { NextRequest, NextResponse } from 'next/server';
import { spawn, exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs';

const execAsync = promisify(exec);

// Get the project root directory (parent of frontend-next)
const PROJECT_ROOT = path.resolve(process.cwd(), '..');

interface ServiceResult {
  success: boolean;
  message: string;
  service: string;
  details?: string;
}

// Check if a process is running on a specific port
async function isPortInUse(port: number): Promise<boolean> {
  try {
    if (process.platform === 'win32') {
      const { stdout } = await execAsync(`netstat -ano | findstr :${port}`);
      return stdout.trim().length > 0;
    } else {
      const { stdout } = await execAsync(`lsof -i :${port}`);
      return stdout.trim().length > 0;
    }
  } catch {
    return false;
  }
}

// Start the FastAPI backend
async function startBackend(): Promise<ServiceResult> {
  try {
    // Check if already running
    if (await isPortInUse(8001)) {
      return {
        success: true,
        service: 'backend',
        message: 'Backend zaten çalışıyor (port 8001)',
      };
    }

    // Find the run.py or start script
    const runPyPath = path.join(PROJECT_ROOT, 'run.py');
    const startupBatPath = path.join(PROJECT_ROOT, 'startup.bat');
    const venvPython = path.join(PROJECT_ROOT, '.venv', 'Scripts', 'python.exe');
    const venvPythonUnix = path.join(PROJECT_ROOT, '.venv', 'bin', 'python');

    let pythonPath = 'python';
    if (fs.existsSync(venvPython)) {
      pythonPath = venvPython;
    } else if (fs.existsSync(venvPythonUnix)) {
      pythonPath = venvPythonUnix;
    }

    if (fs.existsSync(runPyPath)) {
      // Start using run.py
      const child = spawn(pythonPath, ['run.py'], {
        cwd: PROJECT_ROOT,
        detached: true,
        stdio: 'ignore',
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
      });
      child.unref();

      // Wait a bit and check if it started
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      if (await isPortInUse(8001)) {
        return {
          success: true,
          service: 'backend',
          message: 'Backend başarıyla başlatıldı!',
          details: `PID: ${child.pid}`,
        };
      } else {
        return {
          success: false,
          service: 'backend',
          message: 'Backend başlatıldı ama henüz hazır değil. Birkaç saniye bekleyin.',
        };
      }
    } else if (process.platform === 'win32' && fs.existsSync(startupBatPath)) {
      // Use startup.bat on Windows
      spawn('cmd.exe', ['/c', 'start', '/min', 'startup.bat'], {
        cwd: PROJECT_ROOT,
        detached: true,
        stdio: 'ignore',
      });

      return {
        success: true,
        service: 'backend',
        message: 'Backend startup.bat ile başlatılıyor...',
      };
    } else {
      return {
        success: false,
        service: 'backend',
        message: 'run.py bulunamadı. Manuel başlatma gerekiyor.',
        details: `Terminal\'de: cd ${PROJECT_ROOT} && python run.py`,
      };
    }
  } catch (error) {
    return {
      success: false,
      service: 'backend',
      message: `Backend başlatma hatası: ${error instanceof Error ? error.message : 'Bilinmeyen hata'}`,
    };
  }
}

// Start Ollama
async function startOllama(): Promise<ServiceResult> {
  try {
    // Check if Ollama is installed
    if (process.platform === 'win32') {
      try {
        await execAsync('where ollama');
      } catch {
        return {
          success: false,
          service: 'ollama',
          message: 'Ollama yüklü değil. Lütfen https://ollama.ai adresinden yükleyin.',
        };
      }
    }

    // Try to start Ollama serve
    const child = spawn('ollama', ['serve'], {
      detached: true,
      stdio: 'ignore',
    });
    child.unref();

    await new Promise(resolve => setTimeout(resolve, 2000));

    // Check if Ollama is responding
    try {
      const response = await fetch('http://localhost:11434/api/tags');
      if (response.ok) {
        return {
          success: true,
          service: 'ollama',
          message: 'Ollama başarıyla başlatıldı!',
        };
      }
    } catch {
      // Still starting...
    }

    return {
      success: true,
      service: 'ollama',
      message: 'Ollama başlatılıyor... Birkaç saniye bekleyin.',
    };
  } catch (error) {
    return {
      success: false,
      service: 'ollama',
      message: `Ollama başlatma hatası: ${error instanceof Error ? error.message : 'Bilinmeyen hata'}`,
    };
  }
}

// Check all services status
async function checkServices(): Promise<{
  backend: boolean;
  ollama: boolean;
  chromadb: boolean;
}> {
  const [backendRunning, ollamaRunning] = await Promise.all([
    isPortInUse(8001),
    (async () => {
      try {
        const res = await fetch('http://localhost:11434/api/tags', { 
          signal: AbortSignal.timeout(2000) 
        });
        return res.ok;
      } catch {
        return false;
      }
    })(),
  ]);

  return {
    backend: backendRunning,
    ollama: ollamaRunning,
    chromadb: backendRunning, // ChromaDB is embedded in backend
  };
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action } = body;

    let result: ServiceResult;

    switch (action) {
      case 'start-backend':
        result = await startBackend();
        break;
      
      case 'start-ollama':
        result = await startOllama();
        break;
      
      case 'start-all':
        const backendResult = await startBackend();
        const ollamaResult = await startOllama();
        result = {
          success: backendResult.success && ollamaResult.success,
          service: 'all',
          message: `Backend: ${backendResult.message} | Ollama: ${ollamaResult.message}`,
        };
        break;
      
      case 'status':
        const status = await checkServices();
        return NextResponse.json({
          success: true,
          services: status,
        });
      
      default:
        result = {
          success: false,
          service: 'unknown',
          message: 'Bilinmeyen aksiyon',
        };
    }

    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json({
      success: false,
      message: `Hata: ${error instanceof Error ? error.message : 'Bilinmeyen hata'}`,
    }, { status: 500 });
  }
}

export async function GET() {
  const status = await checkServices();
  return NextResponse.json({
    success: true,
    services: status,
    projectRoot: PROJECT_ROOT,
  });
}
