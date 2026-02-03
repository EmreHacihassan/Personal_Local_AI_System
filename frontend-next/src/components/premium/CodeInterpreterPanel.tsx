'use client';

import React, { useState, useRef } from 'react';
import { 
  Code2, 
  Play, 
  Trash2, 
  Copy, 
  Check,
  Terminal,
  Loader2,
  AlertTriangle
} from 'lucide-react';

interface CodeInterpreterPanelProps {
  className?: string;
}

interface ExecutionResult {
  success: boolean;
  output: string;
  error: string | null;
  execution_time_ms: number;
  variables: Record<string, any>;
}

export function CodeInterpreterPanel({ className = '' }: CodeInterpreterPanelProps) {
  const [code, setCode] = useState<string>(`# Python Code Interpreter
# Güvenli sandbox ortamında kod çalıştırın

def fibonacci(n):
    """Fibonacci dizisinin ilk n elemanını döndürür"""
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[-1] + fib[-2])
    return fib[:n]

# Sonucu yazdır
result = fibonacci(10)
print(f"İlk 10 Fibonacci sayısı: {result}")
print(f"Toplam: {sum(result)}")
`);
  const [language, setLanguage] = useState<'python' | 'javascript'>('python');
  const [isExecuting, setIsExecuting] = useState(false);
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [copied, setCopied] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const executeCode = async () => {
    setIsExecuting(true);
    setResult(null);

    try {
      const res = await fetch('http://localhost:8000/api/code/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          language,
        }),
      });

      const data = await res.json();
      setResult(data);
    } catch (error) {
      setResult({
        success: false,
        output: '',
        error: `Bağlantı hatası: ${error}`,
        execution_time_ms: 0,
        variables: {},
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const clearCode = () => {
    setCode('');
    setResult(null);
  };

  const copyOutput = () => {
    if (result?.output) {
      navigator.clipboard.writeText(result.output);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const examples = {
    python: [
      {
        name: 'Fibonacci',
        code: `def fibonacci(n):
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[-1] + fib[-2])
    return fib[:n]

print(fibonacci(15))`,
      },
      {
        name: 'Liste İşlemleri',
        code: `numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Filtreleme
evens = [x for x in numbers if x % 2 == 0]
odds = [x for x in numbers if x % 2 != 0]

print(f"Çift sayılar: {evens}")
print(f"Tek sayılar: {odds}")
print(f"Toplam: {sum(numbers)}")
print(f"Ortalama: {sum(numbers)/len(numbers)}")`,
      },
      {
        name: 'JSON İşleme',
        code: `import json

data = {
    "kullanici": "Ali",
    "yas": 30,
    "hobiler": ["okumak", "yüzmek", "kodlamak"],
    "aktif": True
}

# JSON formatla
json_str = json.dumps(data, indent=2, ensure_ascii=False)
print("JSON Çıktısı:")
print(json_str)

# Parse et
parsed = json.loads(json_str)
print(f"\\nHobiler: {', '.join(parsed['hobiler'])}")`,
      },
    ],
    javascript: [
      {
        name: 'Array Methods',
        code: `const numbers = [1, 2, 3, 4, 5];

const doubled = numbers.map(n => n * 2);
const sum = numbers.reduce((a, b) => a + b, 0);
const evens = numbers.filter(n => n % 2 === 0);

console.log('Original:', numbers);
console.log('Doubled:', doubled);
console.log('Sum:', sum);
console.log('Evens:', evens);`,
      },
      {
        name: 'Object İşlemleri',
        code: `const user = {
  name: 'Ali',
  age: 30,
  hobbies: ['reading', 'coding']
};

// Destructuring
const { name, age } = user;
console.log(\`\${name} is \${age} years old\`);

// Spread operator
const updatedUser = { ...user, city: 'Istanbul' };
console.log(JSON.stringify(updatedUser, null, 2));`,
      },
    ],
  };

  return (
    <div className={`bg-gradient-to-br from-green-900/30 to-emerald-900/30 rounded-xl border border-green-500/30 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-500/20 rounded-lg">
            <Code2 className="w-6 h-6 text-green-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Code Interpreter</h2>
            <p className="text-sm text-gray-400">Güvenli sandbox ortamında kod çalıştırın</p>
          </div>
        </div>

        {/* Language Selector */}
        <div className="flex items-center gap-2 bg-white/5 rounded-lg p-1">
          <button
            onClick={() => setLanguage('python')}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              language === 'python' 
                ? 'bg-green-500 text-white' 
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Python
          </button>
          <button
            onClick={() => setLanguage('javascript')}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              language === 'javascript' 
                ? 'bg-green-500 text-white' 
                : 'text-gray-400 hover:text-white'
            }`}
          >
            JavaScript
          </button>
        </div>
      </div>

      {/* Example Buttons */}
      <div className="flex gap-2 p-4 border-b border-white/10 overflow-x-auto">
        <span className="text-sm text-gray-400 mr-2">Örnekler:</span>
        {examples[language].map((example, idx) => (
          <button
            key={idx}
            onClick={() => setCode(example.code)}
            className="px-3 py-1 bg-white/5 hover:bg-white/10 rounded text-sm text-gray-300 whitespace-nowrap"
          >
            {example.name}
          </button>
        ))}
      </div>

      {/* Code Editor */}
      <div className="p-4">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full h-64 bg-black/30 text-green-300 font-mono text-sm p-4 rounded-lg border border-white/10 focus:border-green-500/50 focus:outline-none resize-none"
            placeholder="Kodunuzu buraya yazın..."
            spellCheck={false}
          />
          
          {/* Line numbers would go here in a more complex implementation */}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={clearCode}
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Temizle
          </button>

          <button
            onClick={executeCode}
            disabled={isExecuting || !code.trim()}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-all ${
              isExecuting || !code.trim()
                ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                : 'bg-green-500 hover:bg-green-600 text-white'
            }`}
          >
            {isExecuting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Çalıştırılıyor...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Çalıştır
              </>
            )}
          </button>
        </div>
      </div>

      {/* Output */}
      {result && (
        <div className="border-t border-white/10 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-400">Çıktı</span>
              {result.success ? (
                <span className="text-xs text-green-400">✓ Başarılı ({result.execution_time_ms}ms)</span>
              ) : (
                <span className="text-xs text-red-400">✗ Hata</span>
              )}
            </div>
            <button
              onClick={copyOutput}
              className="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-white"
            >
              {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
              {copied ? 'Kopyalandı' : 'Kopyala'}
            </button>
          </div>

          <div className={`bg-black/30 rounded-lg p-4 font-mono text-sm max-h-48 overflow-y-auto ${
            result.success ? 'text-green-300' : 'text-red-300'
          }`}>
            {result.success ? (
              <pre className="whitespace-pre-wrap">{result.output || '(Çıktı yok)'}</pre>
            ) : (
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <pre className="whitespace-pre-wrap">{result.error}</pre>
              </div>
            )}
          </div>

          {/* Variables */}
          {result.success && result.variables && Object.keys(result.variables).length > 0 && (
            <div className="mt-4">
              <span className="text-sm text-gray-400 mb-2 block">Değişkenler:</span>
              <div className="bg-black/30 rounded-lg p-3 max-h-32 overflow-y-auto">
                {Object.entries(result.variables).map(([key, value]) => (
                  <div key={key} className="flex gap-2 text-sm font-mono">
                    <span className="text-purple-400">{key}</span>
                    <span className="text-gray-500">=</span>
                    <span className="text-green-300">{JSON.stringify(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
