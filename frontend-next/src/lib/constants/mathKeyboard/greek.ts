import { MathKeyboardCategory } from './types';

export const greekSymbols: MathKeyboardCategory = {
  id: 'greek',
  name: 'Yunan',
  icon: 'αβγ',
  symbols: [
    // Küçük Yunan harfleri
    { s: 'α', d: 'Alfa' }, { s: 'β', d: 'Beta' }, { s: 'γ', d: 'Gama' }, { s: 'δ', d: 'Delta' },
    { s: 'ε', d: 'Epsilon' }, { s: 'ϵ', d: 'Epsilon (Alternatif)' }, { s: 'ζ', d: 'Zeta' }, { s: 'η', d: 'Eta' },
    { s: 'θ', d: 'Teta' }, { s: 'ϑ', d: 'Teta (Alternatif)' }, { s: 'ι', d: 'İota' }, { s: 'κ', d: 'Kappa' },
    { s: 'ϰ', d: 'Kappa (Alternatif)' }, { s: 'λ', d: 'Lambda' }, { s: 'μ', d: 'Mü' }, { s: 'ν', d: 'Nü' },
    { s: 'ξ', d: 'Ksi' }, { s: 'ο', d: 'Omikron' }, { s: 'π', d: 'Pi' }, { s: 'ϖ', d: 'Pi (Alternatif/Varpi)' },
    { s: 'ρ', d: 'Ro' }, { s: 'ϱ', d: 'Ro (Alternatif)' }, { s: 'σ', d: 'Sigma' }, { s: 'ς', d: 'Sigma (Son harf)' },
    { s: 'τ', d: 'Tau' }, { s: 'υ', d: 'Upsilon' }, { s: 'φ', d: 'Fi' }, { s: 'ϕ', d: 'Fi (Alternatif)' },
    { s: 'χ', d: 'Ki' }, { s: 'ψ', d: 'Psi' }, { s: 'ω', d: 'Omega' },
    
    // Büyük Yunan harfleri
    { s: 'Α', d: 'Alfa (Büyük)' }, { s: 'Β', d: 'Beta (Büyük)' }, { s: 'Γ', d: 'Gama (Büyük)' }, { s: 'Δ', d: 'Delta (Büyük)' },
    { s: 'Ε', d: 'Epsilon (Büyük)' }, { s: 'Ζ', d: 'Zeta (Büyük)' }, { s: 'Η', d: 'Eta (Büyük)' }, { s: 'Θ', d: 'Teta (Büyük)' },
    { s: 'Ι', d: 'İota (Büyük)' }, { s: 'Κ', d: 'Kappa (Büyük)' }, { s: 'Λ', d: 'Lambda (Büyük)' }, { s: 'Μ', d: 'Mü (Büyük)' },
    { s: 'Ν', d: 'Nü (Büyük)' }, { s: 'Ξ', d: 'Ksi (Büyük)' }, { s: 'Ο', d: 'Omikron (Büyük)' }, { s: 'Π', d: 'Pi (Büyük)' },
    { s: 'Ρ', d: 'Ro (Büyük)' }, { s: 'Σ', d: 'Sigma (Büyük)' }, { s: 'Τ', d: 'Tau (Büyük)' }, { s: 'Υ', d: 'Upsilon (Büyük)' },
    { s: 'Φ', d: 'Fi (Büyük)' }, { s: 'Χ', d: 'Ki (Büyük)' }, { s: 'Ψ', d: 'Psi (Büyük)' }, { s: 'Ω', d: 'Omega (Büyük)' },
    
    // Yaygın matematiksel kullanımlar
    { s: 'Δx', d: 'x değişimi' }, { s: 'Δy', d: 'y değişimi' }, { s: 'Δt', d: 't değişimi' }, { s: 'δx', d: 'küçük x değişimi' },
    { s: 'Σₙ', d: 'n üzerinden toplam' }, { s: 'Πₙ', d: 'n üzerinden çarpım' }, { s: 'λₘₐₓ', d: 'maksimum özdeğer' }, { s: 'λₘᵢₙ', d: 'minimum özdeğer' },
    { s: 'θ₀', d: 'başlangıç açısı' }, { s: 'ω₀', d: 'doğal frekans' }, { s: 'τ₀', d: 'karakteristik zaman' }, { s: 'μ₀', d: 'manyetik sabit' },
    { s: 'ε₀', d: 'elektrik sabiti' }, { s: 'σₓ', d: 'x yönü gerilimi' }, { s: 'ρ₀', d: 'başlangıç yoğunluğu' }, { s: 'α,β,γ', d: 'açı notasyonu' },
  ]
};
