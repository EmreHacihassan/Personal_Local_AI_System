import { MathKeyboardCategory } from './types';

export const linearAlgebraSymbols: MathKeyboardCategory = {
  id: 'linearalgebra',
  name: 'Lineer Cebir',
  icon: '⊗',
  symbols: [
    // Vektör çarpımları
    { s: '⟨v,w⟩', d: 'İç Çarpım' }, { s: 'v⊗w', d: 'Tensör Çarpım' }, { s: 'v×w', d: 'Çapraz Çarpım' }, { s: 'v·w', d: 'Nokta Çarpım' },
    { s: 'v∧w', d: 'Dış Çarpım (Wedge)' }, { s: 'v⊙w', d: 'Hadamard Çarpım' }, { s: '[v,w]', d: 'Lie Bracket' }, { s: '⟪v,w⟫', d: 'İç Çarpım (Alt)' },
    
    // Norm ve metrik
    { s: '‖v‖', d: 'Vektör Normu' }, { s: '‖v‖₁', d: 'L1 Normu' }, { s: '‖v‖₂', d: 'L2 Normu' }, { s: '‖v‖∞', d: 'Sonsuz Normu' },
    { s: '‖A‖', d: 'Matris Normu' }, { s: '‖A‖F', d: 'Frobenius Normu' }, { s: '|v|', d: 'Mutlak Değer' }, { s: 'd(x,y)', d: 'Metrik' },
    
    // Matris operasyonları
    { s: 'det', d: 'Determinant' }, { s: 'det(A)', d: 'A Determinantı' }, { s: '|A|', d: 'Determinant' }, { s: 'tr', d: 'Trace (İz)' },
    { s: 'tr(A)', d: 'A\'nın İzi' }, { s: 'rank', d: 'Rank (Mertebe)' }, { s: 'rank(A)', d: 'A\'nın Rankı' }, { s: 'nullity', d: 'Nullity' },
    { s: 'dim', d: 'Boyut' }, { s: 'dim(V)', d: 'V\'nin Boyutu' }, { s: 'codim', d: 'Kodimension' }, { s: 'deg', d: 'Derece' },
    
    // Kernel, image, span
    { s: 'ker', d: 'Kernel (Çekirdek)' }, { s: 'ker(T)', d: 'T\'nin Kerneli' }, { s: 'Im', d: 'Image (Görüntü)' }, { s: 'Im(T)', d: 'T\'nin Image\'ı' },
    { s: 'span', d: 'Span (Gerilim)' }, { s: 'span{v₁,v₂}', d: 'Vektör Span' }, { s: 'col', d: 'Sütun Uzayı' }, { s: 'row', d: 'Satır Uzayı' },
    { s: 'null', d: 'Null Space' }, { s: 'range', d: 'Range (Aralık)' },
    
    // Matris dönüşümleri
    { s: 'Aᵀ', d: 'Transpoz' }, { s: 'A⁻¹', d: 'Ters Matris' }, { s: 'A*', d: 'Konjuge Transpoz' }, { s: 'Ā', d: 'Kompleks Konjuge' },
    { s: 'A†', d: 'Hermityen Eşlenik' }, { s: 'A⁺', d: 'Moore-Penrose Ters' }, { s: 'Aᴴ', d: 'Hermityen Transpoz' }, { s: 'adj', d: 'Adjoint' },
    { s: 'adj(A)', d: 'A\'nın Adjoint\'i' },
    
    // Özdeğer, özvektör
    { s: 'λ', d: 'Özdeğer' }, { s: 'λᵢ', d: 'i. Özdeğer' }, { s: 'σ(A)', d: 'Spektrum' }, { s: 'ρ(A)', d: 'Spektral Yarıçap' },
    { s: 'eig', d: 'Özdeğerler' }, { s: 'eigₓ', d: 'Özvektör' }, { s: 'diag', d: 'Diagonal' }, { s: 'diag(λ₁,...,λₙ)', d: 'Diagonal Matris' },
    
    // Özel matrisler
    { s: 'I', d: 'Birim Matris' }, { s: 'Iₙ', d: 'n×n Birim' }, { s: '0', d: 'Sıfır Matris' }, { s: 'J', d: 'Jordan Blok' },
    { s: 'P', d: 'Permütasyon' }, { s: 'Q', d: 'Ortogonal Matris' }, { s: 'U', d: 'Unitary Matris' }, { s: 'L', d: 'Alt Üçgen' },
    { s: 'R', d: 'Üst Üçgen' }, { s: 'D', d: 'Diagonal' },
    
    // İlişkiler
    { s: '⊥', d: 'Ortogonal (Dik)' }, { s: '∥', d: 'Paralel' }, { s: '≅', d: 'Eşyapılı (Izomorf)' }, { s: '≃', d: 'Homotopi Eşdeğer' },
    { s: '≈', d: 'Yaklaşık Eşit' }, { s: '∼', d: 'Benzer' }, { s: '≡', d: 'Özdeş' }, { s: '↔', d: 'Bir-Bir Örtüşme' },
    
    // Vektör notasyonu
    { s: '→', d: 'Vektör Ok' }, { s: 'v⃗', d: 'Vektör v' }, { s: 'ê', d: 'Birim Vektör' }, { s: 'î', d: 'i Birim' },
    { s: 'ĵ', d: 'j Birim' }, { s: 'k̂', d: 'k Birim' }, { s: 'n̂', d: 'Normal Vektör' }, { s: 'r⃗', d: 'Konum Vektörü' },
    
    // Matris parantezleri
    { s: '[aᵢⱼ]', d: 'Matris Elemanları' }, { s: '(aᵢⱼ)', d: 'Matris Parantez' }, { s: '‖aᵢⱼ‖', d: 'Determinant' }, { s: '⟦A⟧', d: 'Çift Bracket' },
  ]
};
