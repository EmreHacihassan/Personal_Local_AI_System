import { MathKeyboardCategory } from './types';

export const probabilitySymbols: MathKeyboardCategory = {
  id: 'probability',
  name: 'Olasılık',
  icon: '🎲',
  symbols: [
    // Temel olasılık
    { s: 'P(A)', d: 'Olasılık' }, { s: 'P(A|B)', d: 'Koşullu Olasılık' }, { s: 'P(A∩B)', d: 'Kesişim Olasılığı' }, { s: 'P(A∪B)', d: 'Birleşim Olasılığı' },
    { s: 'P(Aᶜ)', d: 'Tümleyen Olasılığı' }, { s: 'P(A,B)', d: 'Ortak Olasılık' }, { s: 'Pr', d: 'Olasılık (Alternatif)' }, { s: 'ℙ', d: 'Olasılık Ölçümü' },
    
    // Beklenen değer ve moment
    { s: 'E[X]', d: 'Beklenen Değer' }, { s: 'E[X|Y]', d: 'Koşullu Beklenen' }, { s: 'E[X²]', d: 'İkinci Moment' }, { s: 'E[Xⁿ]', d: 'n. Moment' },
    { s: '𝔼[X]', d: 'Beklenen Değer (Alt)' }, { s: 'μ', d: 'Ortalama/Beklenen' }, { s: 'μₓ', d: 'X Ortalaması' }, { s: 'M(t)', d: 'Moment Üreten' },
    
    // Varyans ve standart sapma
    { s: 'Var(X)', d: 'Varyans' }, { s: 'Var(X|Y)', d: 'Koşullu Varyans' }, { s: 'σ²', d: 'Varyans (sigma kare)' }, { s: 'σ²ₓ', d: 'X Varyansı' },
    { s: 'σ', d: 'Standart Sapma' }, { s: 'σₓ', d: 'X Std Sapması' }, { s: 'SD(X)', d: 'Standart Deviasyon' }, { s: 'SE', d: 'Standard Error' },
    
    // Kovaryans ve korelasyon
    { s: 'Cov(X,Y)', d: 'Kovaryans' }, { s: 'ρ', d: 'Korelasyon' }, { s: 'ρₓᵧ', d: 'X-Y Korelasyonu' }, { s: 'Corr(X,Y)', d: 'Korelasyon' },
    { s: 'Σ', d: 'Kovaryans Matrisi' }, { s: 'R', d: 'Korelasyon Matrisi' },
    
    // Dağılımlar
    { s: 'N(μ,σ²)', d: 'Normal Dağılım' }, { s: '𝒩(μ,σ²)', d: 'Normal (Script)' }, { s: 'Z', d: 'Standart Normal' }, { s: 'Φ(z)', d: 'Normal CDF' },
    { s: 'φ(z)', d: 'Normal PDF' }, { s: 'Bin(n,p)', d: 'Binom Dağılımı' }, { s: 'B(n,p)', d: 'Binom' }, { s: 'Poi(λ)', d: 'Poisson Dağılımı' },
    { s: 'Exp(λ)', d: 'Üstel Dağılım' }, { s: 'U(a,b)', d: 'Uniform Dağılım' }, { s: 'Unif(a,b)', d: 'Uniform' }, { s: 'Geo(p)', d: 'Geometrik' },
    { s: 'NB(r,p)', d: 'Negatif Binom' }, { s: 'HG(N,K,n)', d: 'Hipergeometrik' }, { s: 'Multi(n,p)', d: 'Multinomial' },
    
    // Sürekli dağılımlar
    { s: 'χ²', d: 'Ki-Kare' }, { s: 'χ²ₙ', d: 'n s.d. Ki-Kare' }, { s: 'F', d: 'F Dağılımı' }, { s: 'Fₘ,ₙ', d: 'F (m,n s.d.)' },
    { s: 't', d: 't Dağılımı' }, { s: 'tₙ', d: 't (n s.d.)' }, { s: 'Γ(α,β)', d: 'Gamma Dağılımı' }, { s: 'β(α,β)', d: 'Beta Dağılımı' },
    { s: 'Weibull(k,λ)', d: 'Weibull' }, { s: 'Cauchy', d: 'Cauchy Dağılımı' }, { s: 'Pareto', d: 'Pareto Dağılımı' }, { s: 'Logistic', d: 'Lojistik' },
    
    // Özel fonksiyonlar
    { s: 'Γ', d: 'Gamma Fonksiyonu' }, { s: 'Γ(n)', d: 'Gamma(n)' }, { s: 'β', d: 'Beta Fonksiyonu' }, { s: 'B(a,b)', d: 'Beta(a,b)' },
    { s: 'Γ(n)=(n-1)!', d: 'Gamma Faktöriyel' },
    
    // Kombinatorik
    { s: 'nCr', d: 'Kombinasyon' }, { s: 'nPr', d: 'Permütasyon' }, { s: '(ⁿₖ)', d: 'Binom Katsayısı' }, { s: 'C(n,k)', d: 'Kombinasyon' },
    { s: 'P(n,k)', d: 'Permütasyon' }, { s: 'n!', d: 'Faktöriyel' }, { s: '(n)ₖ', d: 'Düşen Faktöriyel' }, { s: '(n)⁽ᵏ⁾', d: 'Yükselen Faktöriyel' },
    
    // Örnek uzay ve olaylar
    { s: 'Ω', d: 'Örnek Uzay' }, { s: 'ω', d: 'Örnek Nokta' }, { s: '∅', d: 'Boş Olay' }, { s: 'Aᶜ', d: 'Tümleyen' },
    { s: 'A∩B', d: 'Kesişim' }, { s: 'A∪B', d: 'Birleşim' }, { s: 'A⊂B', d: 'Alt Küme' }, { s: 'A⊥B', d: 'Bağımsız' },
    
    // Tahmin ve çıkarım
    { s: 'θ̂', d: 'Tahmin Edici' }, { s: 'μ̂', d: 'Örneklem Ort. Tahmini' }, { s: 'σ̂²', d: 'Varyans Tahmini' }, { s: 'MLE', d: 'En Çok Olabilirlik' },
    { s: 'MAP', d: 'Maximum A Posteriori' }, { s: 'ℒ', d: 'Likelihood' }, { s: 'ℓ', d: 'Log-Likelihood' }, { s: 'L(θ|x)', d: 'Likelihood Fonksiyonu' },
    
    // Diğer
    { s: '~', d: 'Dağılımı' }, { s: 'X~N', d: 'X Normal Dağılımlı' }, { s: 'iid', d: 'Bağımsız Özdeş Dağılımlı' }, { s: '⊥⊥', d: 'Bağımsız' },
  ]
};
