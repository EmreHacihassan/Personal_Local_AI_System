import { MathKeyboardCategory } from './types';

export const basicSymbols: MathKeyboardCategory = {
  id: 'basic',
  name: 'Temel',
  icon: '➕',
  symbols: [
    // Dört işlem
    { s: '+', d: 'Artı' }, { s: '−', d: 'Eksi' }, { s: '×', d: 'Çarpı' }, { s: '÷', d: 'Bölü' },
    { s: '±', d: 'Artı Eksi' }, { s: '∓', d: 'Eksi Artı' }, { s: '·', d: 'Nokta Çarpı' }, { s: '∘', d: 'Kompozisyon' },
    
    // Eşitlik ve karşılaştırma
    { s: '=', d: 'Eşit' }, { s: '≠', d: 'Eşit Değil' }, { s: '≈', d: 'Yaklaşık' }, { s: '≡', d: 'Özdeş' },
    { s: '<', d: 'Küçük' }, { s: '>', d: 'Büyük' }, { s: '≤', d: 'Küçük Eşit' }, { s: '≥', d: 'Büyük Eşit' },
    { s: '≪', d: 'Çok Küçük' }, { s: '≫', d: 'Çok Büyük' }, { s: '≲', d: 'Küçük veya Eşdeğer' }, { s: '≳', d: 'Büyük veya Eşdeğer' },
    
    // Kökler
    { s: '√', d: 'Karekök' }, { s: '∛', d: 'Küpkök' }, { s: '∜', d: '4. Kök' }, { s: 'ⁿ√', d: 'n. Kök' },
    
    // Mutlak değer ve fonksiyonlar
    { s: '|x|', d: 'Mutlak Değer' }, { s: '⌊x⌋', d: 'Taban (Floor)' }, { s: '⌈x⌉', d: 'Tavan (Ceiling)' }, { s: '⌊x⌉', d: 'Yuvarlama' },
    
    // Parantezler
    { s: '()', d: 'Parantez' }, { s: '[]', d: 'Köşeli Parantez' }, { s: '{}', d: 'Süslü Parantez' }, { s: '⟨⟩', d: 'Açılı Parantez' },
    
    // Özel sayılar ve sabitler
    { s: '∞', d: 'Sonsuz' }, { s: 'π', d: 'Pi (3.14159...)' }, { s: 'e', d: 'Euler Sayısı (2.71828...)' }, { s: 'φ', d: 'Altın Oran (1.618...)' },
    { s: 'i', d: 'Sanal Birim' }, { s: 'ℯ', d: 'Euler e' }, { s: 'γ', d: 'Euler-Mascheroni' }, { s: 'ℇ', d: 'Euler Sabiti' },
    
    // Faktöriyel ve yüzde
    { s: '!', d: 'Faktöriyel' }, { s: '!!', d: 'Çift Faktöriyel' }, { s: '%', d: 'Yüzde' }, { s: '‰', d: 'Binde' },
    { s: '‱', d: 'On Binde' }, { s: '№', d: 'Numara' }, { s: '∝', d: 'Orantılı' }, { s: '∼', d: 'Benzer' },
  ]
};
