// Matematik Klavyesi Tip Tanımları

export interface MathSymbol {
  s: string;  // symbol - gösterilecek sembol
  d: string;  // description - sembolün açıklaması (tooltip)
}

export interface MathKeyboardCategory {
  id: string;           // Benzersiz kategori ID
  name: string;         // Türkçe kategori adı
  icon?: string;        // Opsiyonel emoji/icon
  symbols: MathSymbol[];
}

export interface KeyboardConfig {
  type: 'math' | 'normal';
  categories: MathKeyboardCategory[];
}
