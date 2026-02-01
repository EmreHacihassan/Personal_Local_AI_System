import { MathKeyboardCategory } from './types';

export const romanNumeralsSymbols: MathKeyboardCategory = {
  id: 'roman',
  name: 'Roma Rakamları',
  icon: 'Ⅻ',
  symbols: [
    // Büyük Roma rakamları (1-12)
    { s: 'Ⅰ', d: '1 (Bir)' }, { s: 'Ⅱ', d: '2 (İki)' }, { s: 'Ⅲ', d: '3 (Üç)' }, { s: 'Ⅳ', d: '4 (Dört)' },
    { s: 'Ⅴ', d: '5 (Beş)' }, { s: 'Ⅵ', d: '6 (Altı)' }, { s: 'Ⅶ', d: '7 (Yedi)' }, { s: 'Ⅷ', d: '8 (Sekiz)' },
    { s: 'Ⅸ', d: '9 (Dokuz)' }, { s: 'Ⅹ', d: '10 (On)' }, { s: 'Ⅺ', d: '11 (On Bir)' }, { s: 'Ⅻ', d: '12 (On İki)' },
    
    // Büyük Roma rakamları (50, 100, 500, 1000)
    { s: 'Ⅼ', d: '50 (Elli)' }, { s: 'Ⅽ', d: '100 (Yüz)' }, { s: 'Ⅾ', d: '500 (Beş Yüz)' }, { s: 'Ⅿ', d: '1000 (Bin)' },
    
    // Küçük Roma rakamları (1-12)
    { s: 'ⅰ', d: '1 (küçük)' }, { s: 'ⅱ', d: '2 (küçük)' }, { s: 'ⅲ', d: '3 (küçük)' }, { s: 'ⅳ', d: '4 (küçük)' },
    { s: 'ⅴ', d: '5 (küçük)' }, { s: 'ⅵ', d: '6 (küçük)' }, { s: 'ⅶ', d: '7 (küçük)' }, { s: 'ⅷ', d: '8 (küçük)' },
    { s: 'ⅸ', d: '9 (küçük)' }, { s: 'ⅹ', d: '10 (küçük)' }, { s: 'ⅺ', d: '11 (küçük)' }, { s: 'ⅻ', d: '12 (küçük)' },
    
    // Küçük Roma rakamları (50, 100, 500, 1000)
    { s: 'ⅼ', d: '50 (küçük)' }, { s: 'ⅽ', d: '100 (küçük)' }, { s: 'ⅾ', d: '500 (küçük)' }, { s: 'ⅿ', d: '1000 (küçük)' },
    
    // Yaygın kombinasyonlar
    { s: 'XIII', d: '13' }, { s: 'XIV', d: '14' }, { s: 'XV', d: '15' }, { s: 'XVI', d: '16' },
    { s: 'XVII', d: '17' }, { s: 'XVIII', d: '18' }, { s: 'XIX', d: '19' }, { s: 'XX', d: '20' },
    { s: 'XXI', d: '21' }, { s: 'XXV', d: '25' }, { s: 'XXX', d: '30' }, { s: 'XL', d: '40' },
    { s: 'LX', d: '60' }, { s: 'LXX', d: '70' }, { s: 'LXXX', d: '80' }, { s: 'XC', d: '90' },
    { s: 'CC', d: '200' }, { s: 'CCC', d: '300' }, { s: 'CD', d: '400' }, { s: 'DC', d: '600' },
    { s: 'DCC', d: '700' }, { s: 'DCCC', d: '800' }, { s: 'CM', d: '900' }, { s: 'MM', d: '2000' },
    { s: 'MMM', d: '3000' }, { s: 'MMXXIV', d: '2024' }, { s: 'MMXXV', d: '2025' }, { s: 'MMXXVI', d: '2026' },
  ]
};
