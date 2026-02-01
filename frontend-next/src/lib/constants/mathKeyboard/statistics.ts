import { MathKeyboardCategory } from './types';

export const statisticsSymbols: MathKeyboardCategory = {
  id: 'statistics',
  name: 'İstatistik',
  icon: '📊',
  symbols: [
    // Örneklem istatistikleri
    { s: 'x̄', d: 'Örneklem Ortalaması' }, { s: 'ȳ', d: 'Y Ortalaması' }, { s: 's²', d: 'Örneklem Varyansı' }, { s: 's', d: 'Örneklem Std Sapması' },
    { s: 'sₓ', d: 'X Std Sapması' }, { s: 'sᵧ', d: 'Y Std Sapması' }, { s: 'n', d: 'Örneklem Boyutu' }, { s: 'N', d: 'Popülasyon Boyutu' },
    { s: 'r', d: 'Örneklem Korelasyon' }, { s: 'r²', d: 'R Kare' }, { s: 'R²', d: 'R Kare (Büyük)' }, { s: 'R²adj', d: 'Düzeltilmiş R Kare' },
    
    // Hipotez testi
    { s: 'H₀', d: 'Null Hipotez' }, { s: 'H₁', d: 'Alternatif Hipotez' }, { s: 'Hₐ', d: 'Alternatif (a)' }, { s: 'α', d: 'Anlamlılık Düzeyi' },
    { s: 'β', d: 'Tip II Hata' }, { s: '1-β', d: 'Güç' }, { s: 'p', d: 'p Değeri' }, { s: 'p-value', d: 'p Değeri' },
    { s: 'α=0.05', d: '%5 Anlamlılık' }, { s: 'α=0.01', d: '%1 Anlamlılık' }, { s: 'reject H₀', d: 'H₀ Reddet' }, { s: 'fail to reject', d: 'H₀ Kabul' },
    
    // Güven aralığı
    { s: 'CI', d: 'Güven Aralığı' }, { s: '95% CI', d: '%95 Güven Aralığı' }, { s: '99% CI', d: '%99 Güven Aralığı' }, { s: '[a,b]', d: 'Aralık' },
    { s: 'x̄±ME', d: 'Ortalama ± Hata Payı' }, { s: 'ME', d: 'Margin of Error' }, { s: 'zα/2', d: 'Kritik z Değeri' }, { s: 'tα/2,df', d: 'Kritik t Değeri' },
    
    // Test istatistikleri
    { s: 'z', d: 'z Skoru' }, { s: 'z-score', d: 'z Skoru' }, { s: 't', d: 't İstatistiği' }, { s: 't-stat', d: 't İstatistiği' },
    { s: 'χ²', d: 'Ki-Kare İstatistiği' }, { s: 'χ²-stat', d: 'Ki-Kare İstat.' }, { s: 'F', d: 'F İstatistiği' }, { s: 'F-stat', d: 'F İstatistiği' },
    { s: 'U', d: 'Mann-Whitney U' }, { s: 'W', d: 'Wilcoxon W' }, { s: 'K-S', d: 'Kolmogorov-Smirnov' }, { s: 'D', d: 'K-S İstatistiği' },
    
    // Regresyon
    { s: 'ŷ', d: 'Tahmin Edilen Y' }, { s: 'β₀', d: 'Y-Kesişim' }, { s: 'β₁', d: 'Eğim' }, { s: 'βᵢ', d: 'i. Katsayı' },
    { s: 'b₀', d: 'Örneklem Kesişim' }, { s: 'b₁', d: 'Örneklem Eğim' }, { s: 'ε', d: 'Hata Terimi' }, { s: 'εᵢ', d: 'i. Rezidüel' },
    { s: 'SST', d: 'Toplam Kareler Top.' }, { s: 'SSR', d: 'Regresyon Kar. Top.' }, { s: 'SSE', d: 'Hata Kareler Top.' }, { s: 'MSR', d: 'Regresyon Ort. Kare' },
    { s: 'MSE', d: 'Hata Ort. Kare' }, { s: 'RMSE', d: 'Kök Ort. Kare Hata' }, { s: 'MAE', d: 'Ort. Mutlak Hata' }, { s: 'MAPE', d: 'Ort. Mutlak Yüzde Hata' },
    
    // Serbestlik derecesi
    { s: 'df', d: 'Serbestlik Derecesi' }, { s: 'df=n-1', d: 's.d. = n-1' }, { s: 'ν', d: 'Serbestlik Der. (nu)' }, { s: 'n-k-1', d: 'Regresyon s.d.' },
    
    // Model seçimi
    { s: 'AIC', d: 'Akaike IC' }, { s: 'BIC', d: 'Bayesian IC' }, { s: 'Cp', d: "Mallow's Cp" }, { s: 'adj R²', d: 'Düzeltilmiş R²' },
    
    // Tanımlayıcı istatistikler
    { s: 'Q₁', d: '1. Çeyrek (25%)' }, { s: 'Q₂', d: '2. Çeyrek (Medyan)' }, { s: 'Q₃', d: '3. Çeyrek (75%)' }, { s: 'IQR', d: 'Çeyrekler Arası' },
    { s: 'Med', d: 'Medyan' }, { s: 'mode', d: 'Mod' }, { s: 'range', d: 'Aralık' }, { s: 'min', d: 'Minimum' },
    { s: 'max', d: 'Maksimum' }, { s: 'CV', d: 'Varyasyon Katsayısı' }, { s: 'skew', d: 'Çarpıklık' }, { s: 'kurt', d: 'Basıklık' },
    { s: 'γ₁', d: 'Çarpıklık (gamma)' }, { s: 'γ₂', d: 'Basıklık (gamma)' }, { s: 'Σxᵢ', d: 'Toplam' }, { s: 'Σxᵢ²', d: 'Kareler Toplamı' },
    
    // ANOVA
    { s: 'ANOVA', d: 'Varyans Analizi' }, { s: 'SSB', d: 'Gruplar Arası SS' }, { s: 'SSW', d: 'Gruplar İçi SS' }, { s: 'MSB', d: 'Gruplar Arası MS' },
    { s: 'MSW', d: 'Gruplar İçi MS' }, { s: 'k', d: 'Grup Sayısı' }, { s: 'nᵢ', d: 'i. Grup Boyutu' }, { s: 'x̄ᵢ', d: 'i. Grup Ort.' },
    
    // Bayesian
    { s: 'P(θ|x)', d: 'Posterior' }, { s: 'P(x|θ)', d: 'Likelihood' }, { s: 'P(θ)', d: 'Prior' }, { s: 'π(θ)', d: 'Prior Dağılım' },
    { s: 'π(θ|x)', d: 'Posterior Dağılım' }, { s: 'L(θ;x)', d: 'Likelihood Fonk.' },
  ]
};
