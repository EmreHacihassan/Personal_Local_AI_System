import { MathKeyboardCategory } from './types';

export const bracketsSymbols: MathKeyboardCategory = {
  id: 'brackets',
  name: 'Parantezler',
  icon: '⟨⟩',
  symbols: [
    // Standart parantezler
    { s: '(', d: 'Sol Parantez' }, { s: ')', d: 'Sağ Parantez' }, { s: '()', d: 'Parantez Çifti' }, { s: '( )', d: 'Boşluklu Parantez' },
    { s: '[', d: 'Sol Köşeli' }, { s: ']', d: 'Sağ Köşeli' }, { s: '[]', d: 'Köşeli Çifti' }, { s: '[ ]', d: 'Boşluklu Köşeli' },
    { s: '{', d: 'Sol Süslü' }, { s: '}', d: 'Sağ Süslü' }, { s: '{}', d: 'Süslü Çifti' }, { s: '{ }', d: 'Boşluklu Süslü' },
    
    // Açılı parantezler
    { s: '⟨', d: 'Sol Açılı' }, { s: '⟩', d: 'Sağ Açılı' }, { s: '⟨⟩', d: 'Açılı Çifti' }, { s: '⟨ ⟩', d: 'Boşluklu Açılı' },
    { s: '〈', d: 'Sol Açılı (Alt)' }, { s: '〉', d: 'Sağ Açılı (Alt)' }, { s: '〈〉', d: 'Açılı Çifti (Alt)' },
    { s: '<', d: 'Küçüktür (Açılı)' }, { s: '>', d: 'Büyüktür (Açılı)' }, { s: '<>', d: 'Açılı (ASCII)' },
    
    // Çift parantezler
    { s: '⟪', d: 'Sol Çift Açılı' }, { s: '⟫', d: 'Sağ Çift Açılı' }, { s: '⟪⟫', d: 'Çift Açılı' }, { s: '《', d: 'Sol Çift Açılı (CJK)' },
    { s: '》', d: 'Sağ Çift Açılı (CJK)' }, { s: '«', d: 'Sol Guillemet' }, { s: '»', d: 'Sağ Guillemet' }, { s: '«»', d: 'Guillemet Çifti' },
    { s: '‹', d: 'Sol Tek Guillemet' }, { s: '›', d: 'Sağ Tek Guillemet' }, { s: '‹›', d: 'Tek Guillemet' },
    
    // Tavan ve taban
    { s: '⌊', d: 'Sol Taban' }, { s: '⌋', d: 'Sağ Taban' }, { s: '⌊⌋', d: 'Taban (Floor)' }, { s: '⌊x⌋', d: 'x\'in Tabanı' },
    { s: '⌈', d: 'Sol Tavan' }, { s: '⌉', d: 'Sağ Tavan' }, { s: '⌈⌉', d: 'Tavan (Ceiling)' }, { s: '⌈x⌉', d: 'x\'in Tavanı' },
    
    // Çift köşeli (semantik)
    { s: '⟦', d: 'Sol Çift Köşeli' }, { s: '⟧', d: 'Sağ Çift Köşeli' }, { s: '⟦⟧', d: 'Semantik Parantez' }, { s: '⟦x⟧', d: 'x\'in Anlamı' },
    { s: '⌜', d: 'Sol Üst Köşe' }, { s: '⌝', d: 'Sağ Üst Köşe' }, { s: '⌞', d: 'Sol Alt Köşe' }, { s: '⌟', d: 'Sağ Alt Köşe' },
    { s: '⌜⌝', d: 'Üst Köşeler' }, { s: '⌞⌟', d: 'Alt Köşeler' },
    
    // Dikey çizgiler (mutlak değer vb.)
    { s: '|', d: 'Dikey Çizgi' }, { s: '‖', d: 'Çift Dikey' }, { s: '|x|', d: 'Mutlak Değer' }, { s: '‖x‖', d: 'Norm' },
    { s: '|||', d: 'Üçlü Dikey' }, { s: '¦', d: 'Kesik Dikey' }, { s: '┃', d: 'Kalın Dikey' }, { s: '┆', d: 'Noktalı Dikey' },
    
    // Özel parantezler
    { s: '⦃', d: 'Sol Beyaz Süslü' }, { s: '⦄', d: 'Sağ Beyaz Süslü' }, { s: '⦅', d: 'Sol Beyaz Parantez' }, { s: '⦆', d: 'Sağ Beyaz Parantez' },
    { s: '⦇', d: 'Sol Z Notasyonu' }, { s: '⦈', d: 'Sağ Z Notasyonu' }, { s: '⦉', d: 'Sol Açı Z' }, { s: '⦊', d: 'Sağ Açı Z' },
    { s: '⦋', d: 'Sol Açılı Köşeli' }, { s: '⦌', d: 'Sağ Açılı Köşeli' }, { s: '⦍', d: 'Sol Açılı Köşeli 2' }, { s: '⦎', d: 'Sağ Açılı Köşeli 2' },
    
    // Bra-ket notasyonu (Kuantum)
    { s: '|ψ⟩', d: 'Ket Psi' }, { s: '⟨ψ|', d: 'Bra Psi' }, { s: '⟨ψ|φ⟩', d: 'İç Çarpım' }, { s: '|0⟩', d: 'Ket Sıfır' },
    { s: '|1⟩', d: 'Ket Bir' }, { s: '|n⟩', d: 'Ket n' }, { s: '⟨n|', d: 'Bra n' }, { s: '|ψ⟩⟨ψ|', d: 'Projeksiyon' },
    
    // Matematiksel kullanımlar
    { s: '(a,b)', d: 'Açık Aralık' }, { s: '[a,b]', d: 'Kapalı Aralık' }, { s: '[a,b)', d: 'Yarı Açık (sol kapalı)' }, { s: '(a,b]', d: 'Yarı Açık (sağ kapalı)' },
    { s: '(x,y)', d: 'Sıralı İkili' }, { s: '⟨x,y⟩', d: 'İç Çarpım' }, { s: '[x,y]', d: 'Kapalı Aralık' }, { s: '{x,y}', d: 'Küme' },
    { s: '(ⁿₖ)', d: 'Binom Katsayısı' }, { s: '[aᵢⱼ]', d: 'Matris' }, { s: '|aᵢⱼ|', d: 'Determinant' }, { s: '‖A‖', d: 'Matris Normu' },
  ]
};
