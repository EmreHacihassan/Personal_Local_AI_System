import { MathKeyboardCategory } from './types';

export const setsSymbols: MathKeyboardCategory = {
  id: 'sets',
  name: 'Kümeler',
  icon: '∪',
  symbols: [
    // Eleman ilişkileri
    { s: '∈', d: 'Elemanı' }, { s: '∉', d: 'Elemanı Değil' }, { s: '∋', d: 'İçerir' }, { s: '∌', d: 'İçermez' },
    { s: 'x∈A', d: 'x A elemanı' }, { s: 'x∉A', d: 'x A elemanı değil' },
    
    // Alt küme ilişkileri
    { s: '⊂', d: 'Öz Alt Küme' }, { s: '⊃', d: 'Öz Üst Küme' }, { s: '⊆', d: 'Alt Küme veya Eşit' }, { s: '⊇', d: 'Üst Küme veya Eşit' },
    { s: '⊄', d: 'Alt Küme Değil' }, { s: '⊅', d: 'Üst Küme Değil' }, { s: '⊈', d: 'Alt Küme veya Eşit Değil' }, { s: '⊉', d: 'Üst Küme veya Eşit Değil' },
    { s: '⋐', d: 'Çift Alt Küme' }, { s: '⋑', d: 'Çift Üst Küme' }, { s: 'A⊂B', d: 'A, B\'nin alt kümesi' },
    
    // Küme operasyonları
    { s: '∪', d: 'Birleşim' }, { s: '∩', d: 'Kesişim' }, { s: '∖', d: 'Fark (A\\B)' }, { s: '△', d: 'Simetrik Fark' },
    { s: '⊖', d: 'Simetrik Fark (Alt)' }, { s: '×', d: 'Kartezyen Çarpım' }, { s: 'A×B', d: 'A çarpı B' }, { s: '⊎', d: 'Ayrık Birleşim' },
    { s: '⋃', d: 'Büyük Birleşim' }, { s: '⋂', d: 'Büyük Kesişim' }, { s: '⋃ᵢAᵢ', d: 'Tüm Aᵢ Birleşimi' }, { s: '⋂ᵢAᵢ', d: 'Tüm Aᵢ Kesişimi' },
    
    // Tümleyen ve güç kümesi
    { s: 'Aᶜ', d: 'Tümleyen' }, { s: "A'", d: 'Tümleyen (Primer)' }, { s: 'Ā', d: 'Tümleyen (Çizgili)' }, { s: '℘(A)', d: 'Güç Kümesi' },
    { s: '𝒫(A)', d: 'Güç Kümesi' }, { s: '2^A', d: 'Güç Kümesi' }, { s: '|℘(A)|=2^n', d: 'Güç Kümesi Boyutu' },
    
    // Özel kümeler
    { s: '∅', d: 'Boş Küme' }, { s: '{}', d: 'Boş Küme' }, { s: 'ℕ', d: 'Doğal Sayılar' }, { s: 'ℕ₀', d: 'Doğal Sayılar (0 dahil)' },
    { s: 'ℕ⁺', d: 'Pozitif Doğal Sayılar' }, { s: 'ℤ', d: 'Tam Sayılar' }, { s: 'ℤ⁺', d: 'Pozitif Tam Sayılar' }, { s: 'ℤ⁻', d: 'Negatif Tam Sayılar' },
    { s: 'ℚ', d: 'Rasyonel Sayılar' }, { s: 'ℚ⁺', d: 'Pozitif Rasyoneller' }, { s: 'ℝ', d: 'Reel Sayılar' }, { s: 'ℝ⁺', d: 'Pozitif Reeller' },
    { s: 'ℝ⁺₀', d: 'Negatif Olmayan Reeller' }, { s: 'ℂ', d: 'Kompleks Sayılar' }, { s: 'ℍ', d: 'Kuaterniyonlar' }, { s: '𝕆', d: 'Oktonionlar' },
    { s: '𝔽', d: 'Sonlu Cisim' }, { s: 'ℙ', d: 'Asal Sayılar' }, { s: 'ℤₚ', d: 'p modül' }, { s: '𝔽ₚ', d: 'p Elemanlı Cisim' },
    
    // Kardinalite
    { s: '|A|', d: 'Kardinalite' }, { s: '#A', d: 'Eleman Sayısı' }, { s: 'card(A)', d: 'Kardinalite' }, { s: 'n(A)', d: 'Eleman Sayısı' },
    { s: 'ℵ₀', d: 'Alef Sıfır (Sayılabilir)' }, { s: 'ℵ₁', d: 'Alef Bir' }, { s: 'ℵ', d: 'Alef' }, { s: 'c', d: 'Continuum' },
    { s: '|ℕ|=ℵ₀', d: 'Doğal Sayılar Sayılabilir' }, { s: '|ℝ|=c', d: 'Reeller Sayılamaz' }, { s: '2^ℵ₀=c', d: 'Continuum Hipotezi' },
    
    // Niceleyiciler
    { s: '∀', d: 'Her Bir (Tüm)' }, { s: '∃', d: 'Var (En Az Bir)' }, { s: '∄', d: 'Yok (Hiçbir)' }, { s: '∃!', d: 'Tek Bir Tane Var' },
    { s: '∀x∈A', d: 'Her x A\'da' }, { s: '∃x∈A', d: 'A\'da bir x var' }, { s: '∀x:P(x)', d: 'Tüm x için P(x)' }, { s: '∃x:P(x)', d: 'P(x) olan x var' },
    
    // Küme notasyonu
    { s: '{x|P(x)}', d: 'Küme Oluşturucu' }, { s: '{x:P(x)}', d: 'Küme Oluşturucu' }, { s: '{x∈A|P(x)}', d: 'Koşullu Küme' }, { s: '{a,b,c}', d: 'Listeleme' },
    { s: '{1,2,...,n}', d: 'Sonlu Küme' }, { s: '{1,2,3,...}', d: 'Sonsuz Küme' }, { s: '[a,b]', d: 'Kapalı Aralık' }, { s: '(a,b)', d: 'Açık Aralık' },
    { s: '[a,b)', d: 'Yarı Açık (sol kapalı)' }, { s: '(a,b]', d: 'Yarı Açık (sağ kapalı)' }, { s: '(-∞,a]', d: 'Sol Sonsuz' }, { s: '[a,∞)', d: 'Sağ Sonsuz' },
    
    // Eşitlik
    { s: 'A=B', d: 'Eşit Kümeler' }, { s: 'A≠B', d: 'Farklı Kümeler' }, { s: 'A≡B', d: 'Özdeş Kümeler' }, { s: 'A∼B', d: 'Eşkardinal' },
  ]
};
