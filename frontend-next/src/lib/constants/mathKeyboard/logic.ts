import { MathKeyboardCategory } from './types';

export const logicSymbols: MathKeyboardCategory = {
  id: 'logic',
  name: 'Mantık',
  icon: '∧',
  symbols: [
    // Temel mantık bağlaçları
    { s: '∧', d: 'Ve (Konjunktion)' }, { s: '∨', d: 'Veya (Disjunktion)' }, { s: '¬', d: 'Değil (Negasyon)' }, { s: '~', d: 'Değil (Alternatif)' },
    { s: '!', d: 'Değil (Programlama)' }, { s: '⊻', d: 'XOR (Dışlayan Veya)' }, { s: '⊕', d: 'XOR (Daire)' }, { s: '⊼', d: 'NAND' },
    { s: '⊽', d: 'NOR' }, { s: '↑', d: 'NAND (Sheffer)' }, { s: '↓', d: 'NOR (Peirce)' },
    
    // Koşullu ve çift koşullu
    { s: '→', d: 'İse (Koşullu)' }, { s: '⇒', d: 'İse (Çift Ok)' }, { s: '⊃', d: 'İse (Horseshoe)' }, { s: '⟶', d: 'İse (Uzun Ok)' },
    { s: '↔', d: 'Ancak Ve Ancak' }, { s: '⇔', d: 'Eşdeğer (Çift Ok)' }, { s: '≡', d: 'Mantıksal Eşdeğerlik' }, { s: '⟷', d: 'Uzun Çift Ok' },
    { s: '←', d: 'Tersine İse' }, { s: '⇐', d: 'Tersine İse (Çift)' }, { s: '⊂', d: 'Alt Küme (Koşullu)' },
    
    // Niceleyiciler
    { s: '∀', d: 'Tümel Niceleyici (Her)' }, { s: '∃', d: 'Tikel Niceleyici (Var)' }, { s: '∄', d: 'Yok (Değil Var)' }, { s: '∃!', d: 'Tek Var' },
    { s: '∀x', d: 'Her x için' }, { s: '∃x', d: 'Bir x var ki' }, { s: '∀x∈S', d: 'S\'deki her x' }, { s: '∃x∈S', d: 'S\'de bir x var' },
    
    // Doğruluk değerleri
    { s: '⊤', d: 'Doğru (Tautoloji)' }, { s: '⊥', d: 'Yanlış (Çelişki)' }, { s: 'T', d: 'Doğru (True)' }, { s: 'F', d: 'Yanlış (False)' },
    { s: '1', d: 'Doğru (Sayısal)' }, { s: '0', d: 'Yanlış (Sayısal)' }, { s: '⫪', d: 'Doğru Üst' }, { s: '⫫', d: 'Yanlış Alt' },
    
    // Modal mantık
    { s: '□', d: 'Zorunlu (Box)' }, { s: '◇', d: 'Olası (Diamond)' }, { s: '◻', d: 'Zorunlu (Alt)' }, { s: '◊', d: 'Olası (Alt)' },
    { s: '⬜', d: 'Zorunluluk' }, { s: '⬡', d: 'Olasılık' }, { s: '◯', d: 'Sonraki (Temporal)' }, { s: '◁', d: 'Önceki (Temporal)' },
    
    // Çıkarım ve kanıt
    { s: '⊢', d: 'Çıkarır (Turnstile)' }, { s: '⊣', d: 'Sol Çıkarır' }, { s: '⊨', d: 'Model (Çift Turnstile)' }, { s: '⊩', d: 'Kuvvetli Model' },
    { s: '⊬', d: 'Çıkarmaz' }, { s: '⊭', d: 'Model Değil' }, { s: '⊧', d: 'Geçerli' }, { s: '⊪', d: 'Üç Turnstile' },
    { s: '∴', d: 'Öyleyse (Therefore)' }, { s: '∵', d: 'Çünkü (Because)' }, { s: '∎', d: 'QED (İspat Sonu)' }, { s: '□', d: 'Halmos (İspat Sonu)' },
    
    // Küme-mantık ilişkisi
    { s: 'P(x)', d: 'Predicate P(x)' }, { s: 'Q(x)', d: 'Predicate Q(x)' }, { s: 'P∧Q', d: 'P ve Q' }, { s: 'P∨Q', d: 'P veya Q' },
    { s: 'P→Q', d: 'P ise Q' }, { s: '¬P', d: 'P değil' }, { s: 'P↔Q', d: 'P ancak ve ancak Q' }, { s: '(P→Q)∧(Q→P)', d: 'Çift Koşullu' },
    
    // Boolean cebir
    { s: 'AND', d: 'Ve (Boolean)' }, { s: 'OR', d: 'Veya (Boolean)' }, { s: 'NOT', d: 'Değil (Boolean)' }, { s: 'XOR', d: 'Dışlayan Veya' },
    { s: 'NAND', d: 'Ve Değil' }, { s: 'NOR', d: 'Veya Değil' }, { s: 'XNOR', d: 'Eşitlik' }, { s: 'IMP', d: 'İse (Boolean)' },
    
    // Lambda kalkülüs
    { s: 'λ', d: 'Lambda' }, { s: 'λx.', d: 'Lambda x' }, { s: '→β', d: 'Beta İndirgeme' }, { s: '=α', d: 'Alfa Eşdeğerlik' },
    { s: '→η', d: 'Eta İndirgeme' }, { s: 'λf.λx.', d: 'Curry' },
  ]
};
