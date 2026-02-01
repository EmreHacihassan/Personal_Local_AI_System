import { MathKeyboardCategory } from './types';

export const numberTheorySymbols: MathKeyboardCategory = {
  id: 'numbertheory',
  name: 'Sayı Teorisi',
  icon: '∣',
  symbols: [
    // Bölünebilirlik
    { s: '∣', d: 'Böler' }, { s: '∤', d: 'Bölmez' }, { s: '|', d: 'Böler (Alt)' }, { s: 'a|b', d: 'a, b\'yi böler' },
    { s: 'a∤b', d: 'a, b\'yi bölmez' }, { s: '÷', d: 'Bölü İşareti' }, { s: 'mod', d: 'Modül' }, { s: 'a mod n', d: 'a mod n' },
    
    // Modüler aritmetik
    { s: '≡', d: 'Kongruans' }, { s: '≢', d: 'Kongruans Değil' }, { s: 'a≡b(mod n)', d: 'a eşdeğer b mod n' }, { s: '(mod n)', d: 'modül n' },
    { s: 'ℤ/nℤ', d: 'Modül n Tamsayılar' }, { s: 'ℤₙ', d: 'n Modülü' }, { s: '[a]ₙ', d: 'a\'nın eşdeğerlik sınıfı' }, { s: 'ā', d: 'Eşdeğerlik sınıfı' },
    
    // EBOB ve EKOK
    { s: 'gcd', d: 'En Büyük Ortak Bölen' }, { s: 'lcm', d: 'En Küçük Ortak Kat' }, { s: 'gcd(a,b)', d: 'a ve b\'nin EBOB\'u' }, { s: 'lcm(a,b)', d: 'a ve b\'nin EKOK\'u' },
    { s: '(a,b)', d: 'EBOB (kısa)' }, { s: '[a,b]', d: 'EKOK (kısa)' }, { s: 'hcf', d: 'En Yüksek Ortak Faktör' }, { s: 'gcf', d: 'En Büyük Ortak Faktör' },
    
    // Asal sayılar
    { s: 'ℙ', d: 'Asal Sayılar Kümesi' }, { s: 'p', d: 'Asal Sayı' }, { s: 'pₙ', d: 'n. Asal Sayı' }, { s: 'p₁', d: 'İlk Asal (2)' },
    { s: 'π(x)', d: 'Asal Sayma Fonksiyonu' }, { s: 'p|n', d: 'p, n\'i böler' }, { s: 'p∤n', d: 'p, n\'i bölmez' }, { s: 'p^a||n', d: 'p^a tam böler' },
    { s: 'coprime', d: 'Aralarında Asal' }, { s: '(a,b)=1', d: 'a ve b aralarında asal' }, { s: '⊥', d: 'Aralarında Asal (sembol)' },
    
    // Euler ve Fermat
    { s: 'φ(n)', d: 'Euler Fi Fonksiyonu' }, { s: 'φ', d: 'Euler Fi' }, { s: 'ϕ(n)', d: 'Euler Fi (alt)' }, { s: 'τ(n)', d: 'Bölen Sayısı' },
    { s: 'σ(n)', d: 'Bölenler Toplamı' }, { s: 'd(n)', d: 'Bölen Sayısı (alt)' }, { s: 'μ(n)', d: 'Möbius Fonksiyonu' }, { s: 'λ(n)', d: 'Liouville Fon.' },
    { s: 'ω(n)', d: 'Farklı Asal Bölen Sayısı' }, { s: 'Ω(n)', d: 'Asal Bölen Sayısı (çokluk)' },
    
    // Faktörizasyon
    { s: 'n=p₁^a₁...pₖ^aₖ', d: 'Asal Faktörizasyon' }, { s: '∏pᵢ^aᵢ', d: 'Asal Çarpım' }, { s: 'n=∏p^vₚ(n)', d: 'Kanonik Form' }, { s: 'vₚ(n)', d: 'p\'nin n\'deki kuvveti' },
    
    // Legendre ve Jacobi
    { s: '(a/p)', d: 'Legendre Sembolü' }, { s: '(a|p)', d: 'Legendre (alt)' }, { s: '(a/n)', d: 'Jacobi Sembolü' }, { s: '(a|n)', d: 'Jacobi (alt)' },
    { s: '(−1/p)', d: 'Quadratic Character' }, { s: '(2/p)', d: 'Quadratic Character 2' },
    
    // Tamsayı fonksiyonları
    { s: '⌊x⌋', d: 'Taban (Floor)' }, { s: '⌈x⌉', d: 'Tavan (Ceiling)' }, { s: '[x]', d: 'Taban (Gauss)' }, { s: '{x}', d: 'Kesirli Kısım' },
    { s: '⌊x⌉', d: 'Yuvarlama' }, { s: 'sgn(x)', d: 'İşaret Fonksiyonu' }, { s: '||x||', d: 'En Yakın Tamsayıya Uzaklık' },
    
    // Diğer fonksiyonlar
    { s: 'ord', d: 'Mertebe' }, { s: 'ordₙ(a)', d: 'a\'nın n modülündeki mertebesi' }, { s: 'ind', d: 'İndeks (Ayrık Log)' }, { s: 'log_g(a)', d: 'Ayrık Logaritma' },
    
    // Özel diziler
    { s: 'Fₙ', d: 'Fibonacci Sayısı' }, { s: 'Lₙ', d: 'Lucas Sayısı' }, { s: 'Bₙ', d: 'Bernoulli Sayısı' }, { s: 'Cₙ', d: 'Catalan Sayısı' },
    { s: 'Mₙ', d: 'Mersenne Sayısı' }, { s: '2ⁿ-1', d: 'Mersenne Formu' }, { s: 'Pₙ', d: 'Asal (sıralı)' }, { s: 'Tₙ', d: 'Üçgensel Sayı' },
    
    // Sayı kümeleri
    { s: 'ℕ', d: 'Doğal Sayılar' }, { s: 'ℤ', d: 'Tam Sayılar' }, { s: 'ℚ', d: 'Rasyonel Sayılar' }, { s: '𝔸', d: 'Cebirsel Sayılar' },
    { s: 'ℝ∖ℚ', d: 'İrrasyonel Sayılar' }, { s: 'ℤ[i]', d: 'Gauss Tamsayıları' }, { s: 'ℤ[ω]', d: 'Eisenstein Tamsayıları' },
  ]
};
