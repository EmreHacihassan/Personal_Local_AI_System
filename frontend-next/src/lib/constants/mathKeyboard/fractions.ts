import { MathKeyboardCategory } from './types';

export const fractionsSymbols: MathKeyboardCategory = {
  id: 'fractions',
  name: 'Kesirler',
  icon: '½',
  symbols: [
    // Temel kesirler
    { s: '½', d: 'Bir Bölü İki' }, { s: '⅓', d: 'Bir Bölü Üç' }, { s: '⅔', d: 'İki Bölü Üç' }, { s: '¼', d: 'Bir Bölü Dört' },
    { s: '¾', d: 'Üç Bölü Dört' }, { s: '⅕', d: 'Bir Bölü Beş' }, { s: '⅖', d: 'İki Bölü Beş' }, { s: '⅗', d: 'Üç Bölü Beş' },
    { s: '⅘', d: 'Dört Bölü Beş' }, { s: '⅙', d: 'Bir Bölü Altı' }, { s: '⅚', d: 'Beş Bölü Altı' }, { s: '⅐', d: 'Bir Bölü Yedi' },
    { s: '⅛', d: 'Bir Bölü Sekiz' }, { s: '⅜', d: 'Üç Bölü Sekiz' }, { s: '⅝', d: 'Beş Bölü Sekiz' }, { s: '⅞', d: 'Yedi Bölü Sekiz' },
    { s: '⅑', d: 'Bir Bölü Dokuz' }, { s: '⅒', d: 'Bir Bölü On' },
    
    // Sıfır kesirler
    { s: '↉', d: 'Sıfır Bölü Üç' },
    
    // Kesir gösterimi
    { s: 'a/b', d: 'a bölü b' }, { s: '―', d: 'Kesir Çizgisi' }, { s: '⁄', d: 'Kesir Slash' }, { s: '∕', d: 'Bölü İşareti' },
    
    // Üst/alt yazı ile kesir oluşturma
    { s: '¹⁄₂', d: '1/2 (kombinasyon)' }, { s: '¹⁄₃', d: '1/3 (kombinasyon)' }, { s: '¹⁄₄', d: '1/4 (kombinasyon)' }, { s: '¹⁄₅', d: '1/5 (kombinasyon)' },
    { s: '²⁄₃', d: '2/3 (kombinasyon)' }, { s: '³⁄₄', d: '3/4 (kombinasyon)' }, { s: '⁴⁄₅', d: '4/5 (kombinasyon)' }, { s: 'ⁿ⁄ₘ', d: 'n/m (kombinasyon)' },
    
    // Ondalık gösterim
    { s: '0.5', d: 'Yarım (ondalık)' }, { s: '0.25', d: 'Çeyrek (ondalık)' }, { s: '0.75', d: 'Üç Çeyrek (ondalık)' }, { s: '0.33...', d: 'Üçte Bir' },
    { s: '0.666...', d: 'Üçte İki' }, { s: '0.1', d: 'Onda Bir' }, { s: '0.2', d: 'Onda İki' }, { s: '0.125', d: 'Sekizde Bir' },
    
    // Yüzde dönüşümler
    { s: '50%', d: 'Yüzde Elli (1/2)' }, { s: '25%', d: 'Yüzde Yirmi Beş (1/4)' }, { s: '75%', d: 'Yüzde Yetmiş Beş (3/4)' }, { s: '33.3%', d: 'Yüzde Otuz Üç (1/3)' },
    { s: '20%', d: 'Yüzde Yirmi (1/5)' }, { s: '10%', d: 'Yüzde On (1/10)' }, { s: '100%', d: 'Yüzde Yüz (1)' }, { s: '200%', d: 'Yüzde İki Yüz (2)' },
    
    // Oran gösterimi
    { s: '1:2', d: 'Bir\'e İki Oranı' }, { s: '1:3', d: 'Bir\'e Üç Oranı' }, { s: '2:3', d: 'İki\'ye Üç Oranı' }, { s: '3:4', d: 'Üç\'e Dört Oranı' },
    { s: 'a:b', d: 'a\'ya b Oranı' }, { s: '∶', d: 'Oran İşareti' }, { s: '∷', d: 'Orantı' }, { s: '∝', d: 'Orantılı' },
  ]
};
