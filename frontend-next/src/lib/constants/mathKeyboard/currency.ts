import { MathKeyboardCategory } from './types';

export const currencySymbols: MathKeyboardCategory = {
  id: 'currency',
  name: 'Para & Özel',
  icon: '€',
  symbols: [
    // Para birimleri
    { s: '$', d: 'Dolar' }, { s: '€', d: 'Euro' }, { s: '£', d: 'İngiliz Sterlini' }, { s: '¥', d: 'Yen / Yuan' },
    { s: '₺', d: 'Türk Lirası' }, { s: '₹', d: 'Hint Rupisi' }, { s: '₽', d: 'Rus Rublesi' }, { s: '₿', d: 'Bitcoin' },
    { s: '¢', d: 'Sent' }, { s: '₩', d: 'Kore Wonu' }, { s: '₴', d: 'Ukrayna Grivnası' }, { s: '₪', d: 'İsrail Şekeli' },
    { s: '฿', d: 'Tayland Bahtı' }, { s: '₫', d: 'Vietnam Dongu' }, { s: '₦', d: 'Nijerya Nairası' }, { s: '₱', d: 'Peso' },
    { s: '₳', d: 'Arjantin Australi' }, { s: '₲', d: 'Paraguay Guaranisi' }, { s: '₡', d: 'Kolon' }, { s: '₸', d: 'Kazak Tengesi' },
    { s: '₮', d: 'Moğol Tugriki' }, { s: '₯', d: 'Yunan Drahmisi' }, { s: '₠', d: 'Avrupa Para Birimi' }, { s: '₤', d: 'Lira (Tarihi)' },
    
    // Telif ve ticari
    { s: '©', d: 'Telif Hakkı' }, { s: '®', d: 'Tescilli Marka' }, { s: '™', d: 'Ticari Marka' }, { s: '℠', d: 'Servis Markası' },
    { s: '℗', d: 'Fonogram Telifi' }, { s: '№', d: 'Numara İşareti' }, { s: '℁', d: 'Adres İşareti' }, { s: '℀', d: 'Hesap' },
    
    // Birimler ve ölçüler
    { s: '°', d: 'Derece' }, { s: '℃', d: 'Santigrat' }, { s: '℉', d: 'Fahrenheit' }, { s: 'K', d: 'Kelvin' },
    { s: 'Ω', d: 'Ohm' }, { s: '℧', d: 'Mho' }, { s: 'µ', d: 'Mikro' }, { s: '㎜', d: 'Milimetre' },
    { s: '㎝', d: 'Santimetre' }, { s: '㎞', d: 'Kilometre' }, { s: '㎡', d: 'Metrekare' }, { s: '㎥', d: 'Metreküp' },
    { s: '㎏', d: 'Kilogram' }, { s: '㎎', d: 'Miligram' }, { s: '㎖', d: 'Mililitre' }, { s: '㏄', d: 'Santimetreküp' },
    
    // Özel semboller
    { s: '§', d: 'Bölüm İşareti' }, { s: '¶', d: 'Paragraf' }, { s: '†', d: 'Hançer' }, { s: '‡', d: 'Çift Hançer' },
    { s: '※', d: 'Referans' }, { s: '⁂', d: 'Asterism' }, { s: '⁕', d: 'Çiçek Asterisk' }, { s: '⁑', d: 'Çift Asterisk' },
    { s: '‽', d: 'Interrobang' }, { s: '⸘', d: 'Ters Interrobang' }, { s: '¡', d: 'Ters Ünlem' }, { s: '¿', d: 'Ters Soru' },
    { s: '‖', d: 'Çift Dikey Çizgi' }, { s: '¦', d: 'Kesik Dikey Çizgi' }, { s: '⁀', d: 'Bağlayıcı' }, { s: '⸺', d: 'İki Em Tire' },
    { s: '—', d: 'Em Tire' }, { s: '–', d: 'En Tire' }, { s: '―', d: 'Yatay Çizgi' }, { s: '‐', d: 'Tire' },
    { s: '•', d: 'Madde İmi' }, { s: '◦', d: 'Beyaz Madde İmi' }, { s: '▪', d: 'Küçük Siyah Kare' }, { s: '▫', d: 'Küçük Beyaz Kare' },
  ]
};
