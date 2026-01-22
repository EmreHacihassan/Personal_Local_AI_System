'use client';

import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Scan, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  FileCode,
  FolderOpen,
  Loader2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Download
} from 'lucide-react';

interface SecurityScannerPanelProps {
  className?: string;
}

interface Vulnerability {
  id: string;
  type: string;
  severity: string;
  title: string;
  description: string;
  file: string;
  line: number;
  code: string;
  recommendation: string;
  cwe_id?: string;
  owasp?: string;
}

interface ScanResult {
  success: boolean;
  scan_id?: string;
  files_scanned?: number;
  vulnerability_count: number;
  summary?: Record<string, number>;
  vulnerabilities: Vulnerability[];
}

export function SecurityScannerPanel({ className = '' }: SecurityScannerPanelProps) {
  const [code, setCode] = useState<string>(`# Örnek güvenlik açığı içeren kod
import os
import pickle

def login(username, password):
    # SQL Injection açığı
    query = "SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (username, password)
    
    # Hardcoded secret
    api_key = "sk-1234567890abcdef"
    
    # Command injection
    os.system("echo " + username)
    
    return True

# Insecure deserialization
data = pickle.loads(user_input)
`);
  const [language, setLanguage] = useState<'python' | 'javascript'>('python');
  const [scanMode, setScanMode] = useState<'code' | 'file' | 'directory'>('code');
  const [filePath, setFilePath] = useState('');
  const [directoryPath, setDirectoryPath] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [expandedVuln, setExpandedVuln] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/security/status');
      const data = await res.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  };

  const scanCode = async () => {
    setIsScanning(true);
    setResult(null);

    try {
      const res = await fetch('http://localhost:8001/api/security/scan/code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language }),
      });

      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error('Scan failed:', error);
    } finally {
      setIsScanning(false);
    }
  };

  const scanFile = async () => {
    if (!filePath) return;
    setIsScanning(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('filepath', filePath);

      const res = await fetch('http://localhost:8001/api/security/scan/file', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error('Scan failed:', error);
    } finally {
      setIsScanning(false);
    }
  };

  const scanDirectory = async () => {
    if (!directoryPath) return;
    setIsScanning(true);
    setResult(null);

    try {
      const res = await fetch('http://localhost:8001/api/security/scan/directory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ directory: directoryPath }),
      });

      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error('Scan failed:', error);
    } finally {
      setIsScanning(false);
    }
  };

  const handleScan = () => {
    switch (scanMode) {
      case 'code':
        scanCode();
        break;
      case 'file':
        scanFile();
        break;
      case 'directory':
        scanDirectory();
        break;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'high':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/50';
      case 'medium':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
      case 'low':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return <XCircle className="w-4 h-4" />;
      case 'medium':
        return <AlertTriangle className="w-4 h-4" />;
      default:
        return <CheckCircle className="w-4 h-4" />;
    }
  };

  return (
    <div className={`bg-gradient-to-br from-red-900/30 to-orange-900/30 rounded-xl border border-red-500/30 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-500/20 rounded-lg">
            <Shield className="w-6 h-6 text-red-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">AI Güvenlik Tarayıcı</h2>
            <p className="text-sm text-gray-400">Kod güvenlik açıklarını tespit edin</p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs ${status?.status === 'available' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
          {status?.total_scans || 0} tarama
        </div>
      </div>

      {/* Scan Mode Tabs */}
      <div className="flex border-b border-white/10">
        {[
          { id: 'code', label: 'Kod', icon: FileCode },
          { id: 'file', label: 'Dosya', icon: FileCode },
          { id: 'directory', label: 'Klasör', icon: FolderOpen },
        ].map((mode) => (
          <button
            key={mode.id}
            onClick={() => setScanMode(mode.id as any)}
            className={`flex items-center gap-2 px-4 py-3 text-sm transition-colors ${
              scanMode === mode.id
                ? 'text-red-400 border-b-2 border-red-400 bg-white/5'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <mode.icon className="w-4 h-4" />
            {mode.label}
          </button>
        ))}
      </div>

      {/* Input Area */}
      <div className="p-4">
        {scanMode === 'code' && (
          <>
            <div className="flex items-center gap-2 mb-3">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as any)}
                className="bg-white/5 text-white rounded px-3 py-1 text-sm border border-white/10"
              >
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
              </select>
            </div>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full h-48 bg-black/30 text-red-300 font-mono text-sm p-4 rounded-lg border border-white/10 focus:border-red-500/50 focus:outline-none resize-none"
              placeholder="Taranacak kodu buraya yapıştırın..."
              spellCheck={false}
            />
          </>
        )}

        {scanMode === 'file' && (
          <div>
            <label className="text-sm text-gray-400 mb-2 block">Dosya Yolu</label>
            <input
              type="text"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              placeholder="C:\path\to\file.py"
              className="w-full bg-white/5 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-red-500/50 focus:outline-none"
            />
          </div>
        )}

        {scanMode === 'directory' && (
          <div>
            <label className="text-sm text-gray-400 mb-2 block">Klasör Yolu</label>
            <input
              type="text"
              value={directoryPath}
              onChange={(e) => setDirectoryPath(e.target.value)}
              placeholder="C:\path\to\project"
              className="w-full bg-white/5 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-red-500/50 focus:outline-none"
            />
          </div>
        )}

        <button
          onClick={handleScan}
          disabled={isScanning}
          className={`w-full mt-4 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-all ${
            isScanning
              ? 'bg-gray-600 cursor-not-allowed text-gray-400'
              : 'bg-red-500 hover:bg-red-600 text-white'
          }`}
        >
          {isScanning ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Taranıyor...
            </>
          ) : (
            <>
              <Scan className="w-5 h-5" />
              Güvenlik Taraması Başlat
            </>
          )}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="border-t border-white/10 p-4">
          {/* Summary */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-400">
                {result.files_scanned && `${result.files_scanned} dosya tarandı • `}
                {result.vulnerability_count} açık bulundu
              </span>
            </div>
            
            {/* Severity Summary */}
            {result.summary && (
              <div className="flex items-center gap-2">
                {Object.entries(result.summary).map(([severity, count]) => (
                  count > 0 && (
                    <span
                      key={severity}
                      className={`px-2 py-1 rounded text-xs ${getSeverityColor(severity)}`}
                    >
                      {count} {severity}
                    </span>
                  )
                ))}
              </div>
            )}
          </div>

          {/* Vulnerabilities List */}
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {result.vulnerabilities.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
                <p className="text-green-400 font-medium">Güvenlik açığı bulunamadı!</p>
                <p className="text-sm text-gray-400 mt-1">Kodunuz güvenli görünüyor.</p>
              </div>
            ) : (
              result.vulnerabilities.map((vuln) => (
                <div
                  key={vuln.id}
                  className={`rounded-lg border ${getSeverityColor(vuln.severity)} bg-white/5 overflow-hidden`}
                >
                  <div
                    className="p-3 cursor-pointer"
                    onClick={() => setExpandedVuln(expandedVuln === vuln.id ? null : vuln.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        {getSeverityIcon(vuln.severity)}
                        <div>
                          <h4 className="font-medium text-white">{vuln.title}</h4>
                          <p className="text-xs text-gray-400 mt-1">
                            Satır {vuln.line} • {vuln.type}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {vuln.cwe_id && (
                          <span className="text-xs text-gray-400">{vuln.cwe_id}</span>
                        )}
                        {expandedVuln === vuln.id ? (
                          <ChevronUp className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        )}
                      </div>
                    </div>
                  </div>

                  {expandedVuln === vuln.id && (
                    <div className="border-t border-white/10 p-3 space-y-3">
                      <div>
                        <h5 className="text-xs text-gray-400 mb-1">Açıklama</h5>
                        <p className="text-sm text-gray-300">{vuln.description}</p>
                      </div>
                      
                      <div>
                        <h5 className="text-xs text-gray-400 mb-1">Kod</h5>
                        <pre className="bg-black/30 rounded p-2 text-xs text-red-300 overflow-x-auto">
                          {vuln.code}
                        </pre>
                      </div>
                      
                      <div>
                        <h5 className="text-xs text-gray-400 mb-1">Öneri</h5>
                        <p className="text-sm text-green-300">{vuln.recommendation}</p>
                      </div>
                      
                      {vuln.owasp && (
                        <div className="flex items-center gap-2 text-xs text-gray-400">
                          <span>OWASP: {vuln.owasp}</span>
                          <a
                            href={`https://owasp.org/Top10/`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-400 hover:underline flex items-center gap-1"
                          >
                            Detaylar <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
