import { MathKeyboardCategory } from './types';

export const geometrySymbols: MathKeyboardCategory = {
  id: 'geometry',
  name: 'Geometri',
  icon: '△',
  symbols: [
    // Temel şekiller
    { s: '△', d: 'Üçgen' }, { s: '▲', d: 'Dolu Üçgen' }, { s: '▷', d: 'Sağ Üçgen' }, { s: '◁', d: 'Sol Üçgen' },
    { s: '▽', d: 'Ters Üçgen' }, { s: '▼', d: 'Dolu Ters Üçgen' }, { s: '⊿', d: 'Dik Üçgen' }, { s: '◬', d: 'İç Noktalı Üçgen' },
    
    // Dörtgenler
    { s: '□', d: 'Kare' }, { s: '■', d: 'Dolu Kare' }, { s: '▢', d: 'Yuvarlak Kare' }, { s: '▣', d: 'Çizgili Kare' },
    { s: '▤', d: 'Yatay Çizgili' }, { s: '▥', d: 'Dikey Çizgili' }, { s: '▦', d: 'Izgara Kare' }, { s: '▧', d: 'Çapraz Çizgili' },
    { s: '▨', d: 'Çapraz Çizgili 2' }, { s: '▩', d: 'Dama' }, { s: '◇', d: 'Eşkenar Dörtgen' }, { s: '◆', d: 'Dolu Eşk. Dörtgen' },
    { s: '◊', d: 'Baklava' }, { s: '▭', d: 'Dikdörtgen' }, { s: '▯', d: 'Dikey Dikdörtgen' }, { s: '▮', d: 'Dolu Dikey Dik.' },
    
    // Daireler
    { s: '○', d: 'Daire' }, { s: '●', d: 'Dolu Daire' }, { s: '◌', d: 'Noktalı Daire' }, { s: '◍', d: 'Dikey Yarım' },
    { s: '◎', d: 'Çift Daire (Hedef)' }, { s: '◉', d: 'Balık Gözü' }, { s: '⊙', d: 'Noktalı Daire' }, { s: '⊚', d: 'Halkalı Daire' },
    { s: '⊛', d: 'Yıldızlı Daire' }, { s: '⊜', d: 'Eşitlikli Daire' }, { s: '⊝', d: 'Çizgili Daire' }, { s: '⦿', d: 'Hedef' },
    { s: '⊖', d: 'Eksi Daire' }, { s: '⊕', d: 'Artı Daire' }, { s: '⊗', d: 'Çarpı Daire' }, { s: '⊘', d: 'Bölü Daire' },
    
    // Yarım daireler ve yaylar
    { s: '◐', d: 'Sol Yarım Dolu' }, { s: '◑', d: 'Sağ Yarım Dolu' }, { s: '◒', d: 'Alt Yarım Dolu' }, { s: '◓', d: 'Üst Yarım Dolu' },
    { s: '◔', d: 'Sol Üst Çeyrek' }, { s: '◕', d: 'Sağ Alt Çeyrek' },
    { s: '⌒', d: 'Yay' }, { s: '⌓', d: 'Alt Yarım Daire' }, { s: '⌢', d: 'Yay (Frown)' }, { s: '⌣', d: 'Yay (Smile)' },
    
    // Açılar
    { s: '∠', d: 'Açı' }, { s: '∡', d: 'Ölçülen Açı' }, { s: '∢', d: 'Küresel Açı' }, { s: '⊾', d: 'Dik Açı' },
    { s: '⊿', d: 'Dik Açı Üçgen' }, { s: '⦛', d: 'Ölçülen Açı' }, { s: '⦜', d: 'Dik Açı Noktalı' }, { s: '⦝', d: 'Ölçülen Dik Açı' },
    { s: '⦞', d: 'Açık Açı' }, { s: '⦟', d: 'Geniş Açı' }, { s: '⦠', d: 'Geri Açı' }, { s: '⦡', d: 'Çift Açı' },
    { s: '90°', d: 'Dik Açı' }, { s: '180°', d: 'Düz Açı' }, { s: '360°', d: 'Tam Açı' }, { s: 'θ', d: 'Açı (Teta)' },
    
    // İlişkiler
    { s: '⊥', d: 'Dik (Perpendicular)' }, { s: '∥', d: 'Paralel' }, { s: '∦', d: 'Paralel Değil' }, { s: '⫽', d: 'Çift Paralel' },
    { s: '≅', d: 'Eşlik (Congruent)' }, { s: '∼', d: 'Benzerlik (Similar)' }, { s: '≈', d: 'Yaklaşık Eşit' }, { s: '≡', d: 'Özdeş' },
    { s: '⋈', d: 'Bowtie' }, { s: '⋉', d: 'Sol Join' }, { s: '⋊', d: 'Sağ Join' },
    
    // Vektörler ve noktalar
    { s: '·', d: 'Nokta' }, { s: '•', d: 'Bullet' }, { s: '∙', d: 'Operatör Nokta' }, { s: '⋅', d: 'Nokta Çarpım' },
    { s: '⃗', d: 'Vektör Ok' }, { s: '→', d: 'Vektör' }, { s: '↔', d: 'Doğru' }, { s: '⟷', d: 'Uzun Doğru' },
    
    // Geometrik operatörler
    { s: 'AB', d: 'Doğru Parçası' }, { s: '|AB|', d: 'Uzunluk' }, { s: 'd(A,B)', d: 'Mesafe' }, { s: 'Area', d: 'Alan' },
    { s: 'Vol', d: 'Hacim' }, { s: 'Perim', d: 'Çevre' }, { s: 'r', d: 'Yarıçap' }, { s: 'd', d: 'Çap' },
    { s: 'h', d: 'Yükseklik' }, { s: 'b', d: 'Taban' }, { s: 'a', d: 'Kenar a' }, { s: 'l', d: 'Uzunluk' },
    { s: 'w', d: 'Genişlik' }, { s: 'A=πr²', d: 'Daire Alanı' }, { s: 'C=2πr', d: 'Çevre' }, { s: 'V=4/3πr³', d: 'Küre Hacmi' },
  ]
};
