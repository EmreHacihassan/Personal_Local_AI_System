import { MathKeyboardCategory } from './types';

export const physicsSymbols: MathKeyboardCategory = {
  id: 'physics',
  name: 'Fizik',
  icon: '⚛',
  symbols: [
    // Temel sabitler
    { s: 'c', d: 'Işık Hızı (3×10⁸ m/s)' }, { s: 'ℏ', d: 'İndirgenmiş Planck (h/2π)' }, { s: 'h', d: 'Planck Sabiti' }, { s: 'kB', d: 'Boltzmann Sabiti' },
    { s: 'G', d: 'Gravitasyon Sabiti' }, { s: 'e', d: 'Elektron Yükü' }, { s: 'mₑ', d: 'Elektron Kütlesi' }, { s: 'mₚ', d: 'Proton Kütlesi' },
    { s: 'NA', d: 'Avogadro Sayısı' }, { s: 'R', d: 'Gaz Sabiti' }, { s: 'μ₀', d: 'Manyetik Geçirgenlik' }, { s: 'ε₀', d: 'Elektrik Sabiti' },
    { s: 'α', d: 'İnce Yapı Sabiti' }, { s: 'σ', d: 'Stefan-Boltzmann' }, { s: 'λ', d: 'Dalga Boyu' }, { s: 'ν', d: 'Frekans (nü)' },
    
    // Kuantum mekaniği
    { s: 'ψ', d: 'Dalga Fonksiyonu' }, { s: 'Ψ', d: 'Dalga Fonksiyonu (Büyük)' }, { s: '|ψ⟩', d: 'Ket (Bra-Ket)' }, { s: '⟨ψ|', d: 'Bra (Bra-Ket)' },
    { s: '⟨ψ|φ⟩', d: 'İç Çarpım' }, { s: '|0⟩', d: 'Zemin Durumu' }, { s: '|1⟩', d: 'Uyarılmış Durum' }, { s: '|n⟩', d: 'n. Durum' },
    { s: 'Ĥ', d: 'Hamilton Operatörü' }, { s: 'p̂', d: 'Momentum Operatörü' }, { s: 'x̂', d: 'Konum Operatörü' }, { s: 'L̂', d: 'Açısal Momentum Op.' },
    { s: 'ℓ', d: 'Kuantum Sayısı ℓ' }, { s: 'mₗ', d: 'Manyetik Kuantum' }, { s: 'mₛ', d: 'Spin Kuantum' }, { s: 's', d: 'Spin' },
    { s: '↑', d: 'Spin Yukarı' }, { s: '↓', d: 'Spin Aşağı' }, { s: '↑↓', d: 'Çift Spin' }, { s: 'ℏω', d: 'Foton Enerjisi' },
    
    // Vektör operatörleri
    { s: '∇', d: 'Gradyan' }, { s: '∇·', d: 'Diverjans' }, { s: '∇×', d: 'Rotasyonel (Curl)' }, { s: '∇²', d: 'Laplacian' },
    { s: '∆', d: 'Laplacian (Delta)' }, { s: '□', d: "d'Alembert Operatörü" }, { s: '∂ₜ', d: 'Zamana Göre Kısmi' }, { s: '∂ₓ', d: "x'e Göre Kısmi" },
    
    // Elektromanyetizma
    { s: 'E⃗', d: 'Elektrik Alan' }, { s: 'B⃗', d: 'Manyetik Alan' }, { s: 'H⃗', d: 'Manyetik Alan Şiddeti' }, { s: 'D⃗', d: 'Elektrik Yer Değiştirme' },
    { s: 'J⃗', d: 'Akım Yoğunluğu' }, { s: 'ρ', d: 'Yük Yoğunluğu' }, { s: 'Φ', d: 'Elektrik Potansiyel' }, { s: 'A⃗', d: 'Vektör Potansiyel' },
    { s: '∮', d: 'Kontur İntegrali' }, { s: '∯', d: 'Yüzey İntegrali' }, { s: 'Φ_B', d: 'Manyetik Akı' }, { s: 'ε', d: 'EMK' },
    
    // Mekanik
    { s: 'F⃗', d: 'Kuvvet' }, { s: 'p⃗', d: 'Momentum' }, { s: 'L⃗', d: 'Açısal Momentum' }, { s: 'τ⃗', d: 'Tork' },
    { s: 'v⃗', d: 'Hız' }, { s: 'a⃗', d: 'İvme' }, { s: 'ω', d: 'Açısal Hız' }, { s: 'α', d: 'Açısal İvme' },
    { s: 'T', d: 'Kinetik Enerji' }, { s: 'U', d: 'Potansiyel Enerji' }, { s: 'E', d: 'Toplam Enerji' }, { s: 'W', d: 'İş' },
    { s: 'P', d: 'Güç' }, { s: 'I', d: 'Atalet Momenti' }, { s: 'm', d: 'Kütle' }, { s: 'g', d: 'Yerçekimi İvmesi' },
    
    // Termodinamik
    { s: 'S', d: 'Entropi' }, { s: 'Q', d: 'Isı' }, { s: 'ΔU', d: 'İç Enerji Değişimi' }, { s: 'ΔH', d: 'Entalpi Değişimi' },
    { s: 'ΔG', d: 'Gibbs Serbest Enerjisi' }, { s: 'ΔS', d: 'Entropi Değişimi' }, { s: 'η', d: 'Verimlilik' }, { s: 'Cₚ', d: 'Isı Kapasitesi (P)' },
    { s: 'Cᵥ', d: 'Isı Kapasitesi (V)' }, { s: 'PV=nRT', d: 'İdeal Gaz' }, { s: 'dQ/dT', d: 'Isı Kapasitesi' },
    
    // Relativite
    { s: 'γ', d: 'Lorentz Faktörü' }, { s: 'β', d: 'v/c Oranı' }, { s: 'τ', d: 'Proper Zaman' }, { s: 'ds²', d: 'Uzay-Zaman Aralığı' },
    { s: 'gμν', d: 'Metrik Tensör' }, { s: 'Rμν', d: 'Ricci Tensör' }, { s: 'Tμν', d: 'Enerji-Momentum Tensör' }, { s: 'Λ', d: 'Kozmolojik Sabit' },
    
    // Birimler
    { s: 'eV', d: 'Elektron Volt' }, { s: 'MeV', d: 'Mega Elektron Volt' }, { s: 'GeV', d: 'Giga Elektron Volt' }, { s: 'Å', d: 'Angstrom' },
    { s: 'fm', d: 'Femtometre' }, { s: 'Hz', d: 'Hertz' }, { s: 'J', d: 'Joule' }, { s: 'W', d: 'Watt' },
    { s: 'N', d: 'Newton' }, { s: 'Pa', d: 'Pascal' }, { s: 'K', d: 'Kelvin' }, { s: 'mol', d: 'Mol' },
  ]
};
