import { MathKeyboardCategory } from './types';

export const trigonometrySymbols: MathKeyboardCategory = {
  id: 'trigonometry',
  name: 'Trigonometri',
  icon: 'sin',
  symbols: [
    // Temel trigonometrik fonksiyonlar
    { s: 'sin', d: 'Sinüs' }, { s: 'cos', d: 'Kosinüs' }, { s: 'tan', d: 'Tanjant' }, { s: 'cot', d: 'Kotanjant' },
    { s: 'sec', d: 'Sekant' }, { s: 'csc', d: 'Kosekant' }, { s: 'cosec', d: 'Kosekant (Alt)' },
    
    // Ters trigonometrik fonksiyonlar
    { s: 'sin⁻¹', d: 'Arksinüs' }, { s: 'cos⁻¹', d: 'Arkkosinüs' }, { s: 'tan⁻¹', d: 'Arktanjant' }, { s: 'cot⁻¹', d: 'Arkkotanjant' },
    { s: 'sec⁻¹', d: 'Arksekant' }, { s: 'csc⁻¹', d: 'Arkkosekant' },
    { s: 'arcsin', d: 'Arksinüs' }, { s: 'arccos', d: 'Arkkosinüs' }, { s: 'arctan', d: 'Arktanjant' }, { s: 'arccot', d: 'Arkkotanjant' },
    { s: 'asin', d: 'Arksinüs (kısa)' }, { s: 'acos', d: 'Arkkosinüs (kısa)' }, { s: 'atan', d: 'Arktanjant (kısa)' }, { s: 'atan2', d: 'İki Argümanlı Arktan' },
    
    // Hiperbolik fonksiyonlar
    { s: 'sinh', d: 'Hiperbolik Sinüs' }, { s: 'cosh', d: 'Hiperbolik Kosinüs' }, { s: 'tanh', d: 'Hiperbolik Tanjant' }, { s: 'coth', d: 'Hiperbolik Kotanjant' },
    { s: 'sech', d: 'Hiperbolik Sekant' }, { s: 'csch', d: 'Hiperbolik Kosekant' },
    
    // Ters hiperbolik fonksiyonlar
    { s: 'sinh⁻¹', d: 'Ters Hip. Sinüs' }, { s: 'cosh⁻¹', d: 'Ters Hip. Kosinüs' }, { s: 'tanh⁻¹', d: 'Ters Hip. Tanjant' }, { s: 'coth⁻¹', d: 'Ters Hip. Kotanjant' },
    { s: 'arsinh', d: 'Alan Hip. Sinüs' }, { s: 'arcosh', d: 'Alan Hip. Kosinüs' }, { s: 'artanh', d: 'Alan Hip. Tanjant' },
    
    // Logaritmik fonksiyonlar
    { s: 'ln', d: 'Doğal Logaritma' }, { s: 'log', d: 'Logaritma' }, { s: 'log₁₀', d: 'Log Base 10' }, { s: 'log₂', d: 'Log Base 2' },
    { s: 'logₐ', d: 'Log Base a' }, { s: 'lg', d: 'Log Base 10' }, { s: 'lb', d: 'Log Base 2 (İkili)' }, { s: 'ln(x)', d: 'x\'in doğal logu' },
    { s: 'e^x', d: 'e üzeri x' }, { s: 'exp(x)', d: 'Eksponansiyel' }, { s: 'exp', d: 'Eksponansiyel' }, { s: '10^x', d: '10 üzeri x' },
    
    // Trigonometrik ifadeler
    { s: 'sin(x)', d: 'x\'in sinüsü' }, { s: 'cos(x)', d: 'x\'in kosinüsü' }, { s: 'tan(x)', d: 'x\'in tanjantı' }, { s: 'sin²(x)', d: 'sinüs kare x' },
    { s: 'cos²(x)', d: 'kosinüs kare x' }, { s: 'tan²(x)', d: 'tanjant kare x' }, { s: 'sin(2x)', d: 'çift açı sinüs' }, { s: 'cos(2x)', d: 'çift açı kosinüs' },
    
    // Açı birimleri
    { s: '°', d: 'Derece' }, { s: 'rad', d: 'Radyan' }, { s: 'π rad', d: 'Pi radyan' }, { s: '360°', d: 'Tam daire' },
    { s: '2π', d: 'Tam daire (rad)' }, { s: '90°', d: 'Dik açı' }, { s: 'π/2', d: 'Dik açı (rad)' }, { s: '180°', d: 'Düz açı' },
    { s: 'π', d: 'Düz açı (rad)' }, { s: '45°', d: '45 derece' }, { s: 'π/4', d: '45° radyan' }, { s: '60°', d: '60 derece' },
    { s: 'π/3', d: '60° radyan' }, { s: '30°', d: '30 derece' }, { s: 'π/6', d: '30° radyan' },
    
    // Trigonometrik değerler
    { s: 'sin(0)=0', d: 'sin 0' }, { s: 'cos(0)=1', d: 'cos 0' }, { s: 'sin(π/2)=1', d: 'sin 90°' }, { s: 'cos(π/2)=0', d: 'cos 90°' },
    { s: 'sin(π/4)=√2/2', d: 'sin 45°' }, { s: 'cos(π/4)=√2/2', d: 'cos 45°' }, { s: 'sin(π/6)=1/2', d: 'sin 30°' }, { s: 'cos(π/6)=√3/2', d: 'cos 30°' },
    { s: 'sin(π/3)=√3/2', d: 'sin 60°' }, { s: 'cos(π/3)=1/2', d: 'cos 60°' },
    
    // Trigonometrik özdeşlikler
    { s: 'sin²+cos²=1', d: 'Temel özdeşlik' }, { s: '1+tan²=sec²', d: 'Sekant özdeşlik' }, { s: '1+cot²=csc²', d: 'Kosekant özdeşlik' },
  ]
};
