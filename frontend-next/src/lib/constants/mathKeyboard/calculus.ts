import { MathKeyboardCategory } from './types';

export const calculusSymbols: MathKeyboardCategory = {
  id: 'calculus',
  name: 'Kalkülüs',
  icon: '∫',
  symbols: [
    // İntegral sembolleri
    { s: '∫', d: 'İntegral' }, { s: '∬', d: 'Çift İntegral' }, { s: '∭', d: 'Üçlü İntegral' }, { s: '∮', d: 'Kontur İntegrali' },
    { s: '∯', d: 'Yüzey İntegrali' }, { s: '∰', d: 'Hacim İntegrali' }, { s: '∱', d: 'Saat Yönü İntegral' }, { s: '∲', d: 'Saat Yönü Kontur' },
    { s: '∳', d: 'Saat Yönü Ters Kontur' }, { s: '⨌', d: 'Dörtlü İntegral' }, { s: '⨍', d: 'Sonlu Parça İntegrali' }, { s: '⨎', d: 'İntegral Ortalama' },
    
    // Türev sembolleri - ÖNEMLİ
    { s: '∂', d: 'Kısmi Türev' }, { s: 'd', d: 'Diferansiyel d' }, { s: 'ⅆ', d: 'Diferansiyel (Italic)' }, { s: 'đ', d: 'd Çizgili' },
    { s: 'd/dx', d: 'x\'e göre Türev' }, { s: 'd/dy', d: 'y\'ye göre Türev' }, { s: 'd/dt', d: 't\'ye göre Türev' }, { s: 'd²/dx²', d: 'İkinci Türev' },
    { s: '∂/∂x', d: 'Kısmi x Türevi' }, { s: '∂/∂y', d: 'Kısmi y Türevi' }, { s: '∂²/∂x²', d: 'İkinci Kısmi' }, { s: '∂²/∂x∂y', d: 'Karma Kısmi' },
    { s: "f'(x)", d: 'Birinci Türev' }, { s: "f''(x)", d: 'İkinci Türev' }, { s: "f'''(x)", d: 'Üçüncü Türev' }, { s: 'f⁽ⁿ⁾(x)', d: 'n. Türev' },
    { s: 'ẋ', d: 'Zaman Türevi (x nokta)' }, { s: 'ẍ', d: 'İkinci Zaman Türevi' }, { s: 'ẏ', d: 'y nokta' }, { s: 'ÿ', d: 'y çift nokta' },
    { s: 'dy/dx', d: 'Leibniz Türev' }, { s: '∂y/∂x', d: 'Kısmi Türev' }, { s: 'Df', d: 'Türev Operatörü' }, { s: 'D²f', d: 'İkinci Türev Op.' },
    
    // Nabla ve vektör operatörleri
    { s: '∇', d: 'Nabla/Gradyan' }, { s: '∇²', d: 'Laplacian' }, { s: '∇·', d: 'Diverjans' }, { s: '∇×', d: 'Rotasyonel (Curl)' },
    { s: 'Δ', d: 'Delta/Laplacian' }, { s: '∆', d: 'Delta Değişim' }, { s: 'δ', d: 'Küçük Delta' }, { s: 'ε', d: 'Epsilon' },
    
    // Limit sembolleri
    { s: 'lim', d: 'Limit' }, { s: '→', d: 'Yaklaşır' }, { s: 'x→0', d: 'x 0\'a yaklaşır' }, { s: 'x→∞', d: 'x sonsuza yaklaşır' },
    { s: 'x→0⁺', d: 'Sağdan yaklaşır' }, { s: 'x→0⁻', d: 'Soldan yaklaşır' }, { s: 'lim sup', d: 'Limit Süpremum' }, { s: 'lim inf', d: 'Limit İnfimum' },
    { s: 'limₙ→∞', d: 'n Sonsuz Limit' }, { s: 'limₓ→ₐ', d: 'x→a Limit' },
    
    // Toplam ve çarpım
    { s: 'Σ', d: 'Toplam' }, { s: '∏', d: 'Çarpım' }, { s: '∐', d: 'Koprodukt' }, { s: '⊕', d: 'Doğrudan Toplam' },
    { s: 'Σₙ₌₁^∞', d: 'Sonsuz Toplam' }, { s: 'Σᵢ₌₁^n', d: 'Sonlu Toplam' }, { s: '∏ᵢ₌₁^n', d: 'Sonlu Çarpım' },
    
    // Sonsuz ve yakınsama
    { s: '∫₀^∞', d: 'Sonsuz İntegral' }, { s: '∫₋∞^∞', d: 'Tam Reel İntegral' }, { s: '∫ₐ^b', d: 'Belirli İntegral' },
    
    // Supremum, infimum
    { s: 'sup', d: 'Supremum' }, { s: 'inf', d: 'İnfimum' }, { s: 'max', d: 'Maksimum' }, { s: 'min', d: 'Minimum' },
    { s: 'arg max', d: 'Argüman Max' }, { s: 'arg min', d: 'Argüman Min' }, { s: 'ess sup', d: 'Esansiyel Sup' }, { s: 'ess inf', d: 'Esansiyel Inf' },
  ]
};
