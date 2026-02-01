import { MathKeyboardCategory } from './types';

export const superscriptSymbols: MathKeyboardCategory = {
  id: 'superscript',
  name: 'Üs/Alt',
  icon: 'ˣ',
  symbols: [
    // Üst indisler (Superscript) - Rakamlar
    { s: '⁰', d: 'Üs 0' }, { s: '¹', d: 'Üs 1' }, { s: '²', d: 'Üs 2' }, { s: '³', d: 'Üs 3' },
    { s: '⁴', d: 'Üs 4' }, { s: '⁵', d: 'Üs 5' }, { s: '⁶', d: 'Üs 6' }, { s: '⁷', d: 'Üs 7' },
    { s: '⁸', d: 'Üs 8' }, { s: '⁹', d: 'Üs 9' },
    
    // Üst indisler - Harfler
    { s: 'ⁿ', d: 'Üs n' }, { s: 'ˣ', d: 'Üs x' }, { s: 'ʸ', d: 'Üs y' }, { s: 'ᶻ', d: 'Üs z' },
    { s: 'ⁱ', d: 'Üs i' }, { s: 'ʲ', d: 'Üs j' }, { s: 'ᵏ', d: 'Üs k' }, { s: 'ˡ', d: 'Üs l' },
    { s: 'ᵐ', d: 'Üs m' }, { s: 'ᵃ', d: 'Üs a' }, { s: 'ᵇ', d: 'Üs b' }, { s: 'ᶜ', d: 'Üs c' },
    { s: 'ᵈ', d: 'Üs d' }, { s: 'ᵉ', d: 'Üs e' }, { s: 'ᶠ', d: 'Üs f' }, { s: 'ᵍ', d: 'Üs g' },
    { s: 'ʰ', d: 'Üs h' }, { s: 'ᵖ', d: 'Üs p' }, { s: 'ʳ', d: 'Üs r' }, { s: 'ˢ', d: 'Üs s' },
    { s: 'ᵗ', d: 'Üs t' }, { s: 'ᵘ', d: 'Üs u' }, { s: 'ᵛ', d: 'Üs v' }, { s: 'ʷ', d: 'Üs w' },
    
    // Üst indisler - Özel
    { s: '⁺', d: 'Üs +' }, { s: '⁻', d: 'Üs -' }, { s: '⁼', d: 'Üs =' }, { s: '⁽', d: 'Üs (' },
    { s: '⁾', d: 'Üs )' },
    
    // Alt indisler (Subscript) - Rakamlar
    { s: '₀', d: 'Alt 0' }, { s: '₁', d: 'Alt 1' }, { s: '₂', d: 'Alt 2' }, { s: '₃', d: 'Alt 3' },
    { s: '₄', d: 'Alt 4' }, { s: '₅', d: 'Alt 5' }, { s: '₆', d: 'Alt 6' }, { s: '₇', d: 'Alt 7' },
    { s: '₈', d: 'Alt 8' }, { s: '₉', d: 'Alt 9' },
    
    // Alt indisler - Harfler
    { s: 'ₐ', d: 'Alt a' }, { s: 'ₑ', d: 'Alt e' }, { s: 'ₕ', d: 'Alt h' }, { s: 'ᵢ', d: 'Alt i' },
    { s: 'ⱼ', d: 'Alt j' }, { s: 'ₖ', d: 'Alt k' }, { s: 'ₗ', d: 'Alt l' }, { s: 'ₘ', d: 'Alt m' },
    { s: 'ₙ', d: 'Alt n' }, { s: 'ₒ', d: 'Alt o' }, { s: 'ₚ', d: 'Alt p' }, { s: 'ᵣ', d: 'Alt r' },
    { s: 'ₛ', d: 'Alt s' }, { s: 'ₜ', d: 'Alt t' }, { s: 'ᵤ', d: 'Alt u' }, { s: 'ᵥ', d: 'Alt v' },
    { s: 'ₓ', d: 'Alt x' },
    
    // Alt indisler - Özel
    { s: '₊', d: 'Alt +' }, { s: '₋', d: 'Alt -' }, { s: '₌', d: 'Alt =' }, { s: '₍', d: 'Alt (' },
    { s: '₎', d: 'Alt )' },
  ]
};
