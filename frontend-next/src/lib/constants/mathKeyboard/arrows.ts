import { MathKeyboardCategory } from './types';

export const arrowsSymbols: MathKeyboardCategory = {
  id: 'arrows',
  name: 'Oklar',
  icon: '→',
  symbols: [
    // Basit oklar
    { s: '→', d: 'Sağ Ok' }, { s: '←', d: 'Sol Ok' }, { s: '↑', d: 'Yukarı Ok' }, { s: '↓', d: 'Aşağı Ok' },
    { s: '↔', d: 'Sol-Sağ Ok' }, { s: '↕', d: 'Yukarı-Aşağı Ok' }, { s: '↗', d: 'Sağ Yukarı' }, { s: '↘', d: 'Sağ Aşağı' },
    { s: '↙', d: 'Sol Aşağı' }, { s: '↖', d: 'Sol Yukarı' },
    
    // Çift oklar (kalın)
    { s: '⇒', d: 'Çift Sağ Ok (İse)' }, { s: '⇐', d: 'Çift Sol Ok' }, { s: '⇑', d: 'Çift Yukarı' }, { s: '⇓', d: 'Çift Aşağı' },
    { s: '⇔', d: 'Çift Sol-Sağ (Ancak ve Ancak)' }, { s: '⇕', d: 'Çift Yukarı-Aşağı' }, { s: '⇗', d: 'Çift Sağ Yukarı' }, { s: '⇘', d: 'Çift Sağ Aşağı' },
    { s: '⇙', d: 'Çift Sol Aşağı' }, { s: '⇖', d: 'Çift Sol Yukarı' },
    
    // Uzun oklar
    { s: '⟶', d: 'Uzun Sağ Ok' }, { s: '⟵', d: 'Uzun Sol Ok' }, { s: '⟷', d: 'Uzun Sol-Sağ' },
    { s: '⟹', d: 'Uzun Çift Sağ (İse)' }, { s: '⟸', d: 'Uzun Çift Sol' }, { s: '⟺', d: 'Uzun Çift Sol-Sağ' },
    
    // Kesikli oklar
    { s: '⇢', d: 'Kesikli Sağ' }, { s: '⇠', d: 'Kesikli Sol' }, { s: '⤍', d: 'Kesikli Sağ Ok' }, { s: '⤌', d: 'Kesikli Sol Ok' },
    
    // Kıvrımlı ve özel oklar
    { s: '↩', d: 'Sol Dönüş' }, { s: '↪', d: 'Sağ Dönüş' }, { s: '↰', d: 'Yukarı Sol Dönüş' }, { s: '↱', d: 'Yukarı Sağ Dönüş' },
    { s: '↲', d: 'Aşağı Sol Dönüş' }, { s: '↳', d: 'Aşağı Sağ Dönüş' }, { s: '⤴', d: 'Sağ Yukarı Kıvrım' }, { s: '⤵', d: 'Sağ Aşağı Kıvrım' },
    { s: '↶', d: 'Saat Yönü Tersine' }, { s: '↷', d: 'Saat Yönünde' }, { s: '↻', d: 'Saat Yönü Döngü' }, { s: '↺', d: 'Saat Yönü Tersine Döngü' },
    
    // Haritalama okları
    { s: '↦', d: 'Eşleme (Mapsto)' }, { s: '↤', d: 'Sol Eşleme' }, { s: '⤇', d: 'Çift Eşleme' }, { s: '⟼', d: 'Uzun Eşleme' },
    { s: '↣', d: 'Sağ Kuyruk Ok' }, { s: '↢', d: 'Sol Kuyruk Ok' }, { s: '↠', d: 'Sağ Çift Baş' }, { s: '↞', d: 'Sol Çift Baş' },
    { s: '↬', d: 'Sağ Döngü Ok' }, { s: '↫', d: 'Sol Döngü Ok' },
    
    // Çoklu ve paralel oklar
    { s: '⇈', d: 'Çift Yukarı' }, { s: '⇊', d: 'Çift Aşağı' }, { s: '⇇', d: 'Çift Sol' }, { s: '⇉', d: 'Çift Sağ' },
    { s: '⇄', d: 'Sağ Sol Karşılıklı' }, { s: '⇆', d: 'Sol Sağ Karşılıklı' }, { s: '⇅', d: 'Yukarı Aşağı' }, { s: '⇵', d: 'Aşağı Yukarı' },
    
    // Matematiksel oklar
    { s: '↝', d: 'Dalgalı Sağ' }, { s: '↜', d: 'Dalgalı Sol' }, { s: '⇝', d: 'Kıvrımlı Sağ' }, { s: '⇜', d: 'Kıvrımlı Sol' },
    { s: '⊸', d: 'Multimap' }, { s: '⟜', d: 'Sol Multimap' }, { s: '⤳', d: 'Dalgalı Ok' }, { s: '⤏', d: 'Çift Kesikli Sağ' },
    
    // Limit ve yaklaşım okları
    { s: '→', d: 'Yaklaşır' }, { s: '⇀', d: 'Harpoon Sağ' }, { s: '↼', d: 'Harpoon Sol' }, { s: '⇁', d: 'Harpoon Sağ Alt' },
    { s: '↽', d: 'Harpoon Sol Alt' }, { s: '⇌', d: 'Denge Oku' }, { s: '⇋', d: 'Ters Denge Oku' }, { s: '⥊', d: 'Sol Sağ Harpoon' },
    
    // Kategori teorisi okları
    { s: '↪', d: 'Kapsama (Inclusion)' }, { s: '↠', d: 'Örten (Surjection)' }, { s: '↣', d: 'Bire-bir Örten' }, { s: '⤖', d: 'Kompozisyon' },
    { s: '⟿', d: 'Çift Çizgi Ok' }, { s: '⤀', d: 'Doğal Dönüşüm' },
  ]
};
