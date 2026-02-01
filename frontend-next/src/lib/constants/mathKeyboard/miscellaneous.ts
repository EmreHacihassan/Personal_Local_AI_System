import { MathKeyboardCategory } from './types';

export const miscellaneousSymbols: MathKeyboardCategory = {
  id: 'misc',
  name: 'Çeşitli',
  icon: '☆',
  symbols: [
    // İspat ve sonuç sembolleri
    { s: '∎', d: 'QED (İspat Sonu)' }, { s: '□', d: 'Halmos (İspat Sonu)' }, { s: '■', d: 'Dolu Kare (İspat)' }, { s: '◼', d: 'Siyah Orta Kare' },
    { s: '◻', d: 'Beyaz Orta Kare' }, { s: '▪', d: 'Küçük Siyah Kare' }, { s: '▫', d: 'Küçük Beyaz Kare' }, { s: 'Q.E.D.', d: 'Quod Erat Demonstrandum' },
    
    // Yıldızlar ve rozet
    { s: '★', d: 'Siyah Yıldız' }, { s: '☆', d: 'Beyaz Yıldız' }, { s: '✦', d: 'Siyah Dört Yıldız' }, { s: '✧', d: 'Beyaz Dört Yıldız' },
    { s: '✪', d: 'Daire İçi Yıldız' }, { s: '✫', d: 'Açık Merkez Yıldız' }, { s: '✬', d: 'Siyah Merkez Yıldız' }, { s: '✭', d: 'Dış Hatları Yıldız' },
    { s: '✮', d: 'Ağır Dış Hatları Yıldız' }, { s: '✯', d: 'Sivri Yıldız' }, { s: '✰', d: 'Gölgeli Yıldız' }, { s: '⁎', d: 'Düşük Asterisk' },
    { s: '*', d: 'Asterisk' }, { s: '∗', d: 'Operatör Asterisk' }, { s: '⁕', d: 'Çiçek Asterisk' }, { s: '⁑', d: 'İki Asterisk' },
    
    // Onay ve işaretler
    { s: '✓', d: 'Onay İşareti' }, { s: '✔', d: 'Kalın Onay' }, { s: '✗', d: 'Çarpı İşareti' }, { s: '✘', d: 'Kalın Çarpı' },
    { s: '✕', d: 'Çarpı (İnce)' }, { s: '☑', d: 'Onaylı Kutu' }, { s: '☐', d: 'Boş Kutu' }, { s: '☒', d: 'Çarpılı Kutu' },
    { s: '⊠', d: 'Çarpılı Kare' }, { s: '⊡', d: 'Noktalı Kare' }, { s: '⊟', d: 'Eksi Kare' }, { s: '⊞', d: 'Artı Kare' },
    
    // Kalpler ve kartlar
    { s: '♠', d: 'Maça' }, { s: '♤', d: 'Beyaz Maça' }, { s: '♣', d: 'Sinek' }, { s: '♧', d: 'Beyaz Sinek' },
    { s: '♥', d: 'Kupa' }, { s: '♡', d: 'Beyaz Kupa' }, { s: '♦', d: 'Karo' }, { s: '♢', d: 'Beyaz Karo' },
    { s: '❤', d: 'Ağır Kalp' }, { s: '❥', d: 'Dönen Kalp' }, { s: '❣', d: 'Ünlemli Kalp' },
    
    // Müzik notaları
    { s: '♩', d: 'Dörtlük Nota' }, { s: '♪', d: 'Sekizlik Nota' }, { s: '♫', d: 'Bağlı Notalar' }, { s: '♬', d: 'On Altılık Notalar' },
    { s: '♭', d: 'Bemol' }, { s: '♮', d: 'Natürel' }, { s: '♯', d: 'Diyez' }, { s: '𝄞', d: 'Sol Anahtarı' },
    
    // Hava durumu ve doğa
    { s: '☀', d: 'Güneş' }, { s: '☁', d: 'Bulut' }, { s: '☂', d: 'Şemsiye' }, { s: '☃', d: 'Kardan Adam' },
    { s: '☄', d: 'Kuyruklu Yıldız' }, { s: '★', d: 'Yıldız' }, { s: '☽', d: 'Hilal (Sol)' }, { s: '☾', d: 'Hilal (Sağ)' },
    { s: '⚡', d: 'Yıldırım' }, { s: '❄', d: 'Kar Tanesi' }, { s: '❅', d: 'Kar Tanesi 2' }, { s: '❆', d: 'Kar Tanesi 3' },
    
    // Oklar ve işaretçiler
    { s: '☛', d: 'Sağ İşaret Eli' }, { s: '☚', d: 'Sol İşaret Eli' }, { s: '☜', d: 'Sol El' }, { s: '☞', d: 'Sağ El' },
    { s: '➔', d: 'Sağ Göstermeli Ok' }, { s: '➜', d: 'Ağır Sağ Ok' }, { s: '➤', d: 'Üçgen Sağ Ok' }, { s: '➥', d: 'Aşağı Kıvrık Ok' },
    
    // Geometrik desenler
    { s: '◆', d: 'Siyah Elmas' }, { s: '◇', d: 'Beyaz Elmas' }, { s: '◈', d: 'Beyaz Elmas İçi Siyah' }, { s: '◉', d: 'Balık Gözü' },
    { s: '◊', d: 'Baklava' }, { s: '○', d: 'Beyaz Daire' }, { s: '●', d: 'Siyah Daire' }, { s: '◌', d: 'Noktalı Daire' },
    { s: '◍', d: 'Dikey Yarım Dolu' }, { s: '◎', d: 'Hedef' }, { s: '◐', d: 'Sol Yarım Siyah' }, { s: '◑', d: 'Sağ Yarım Siyah' },
    
    // Okültür ve din sembolleri
    { s: '☯', d: 'Yin Yang' }, { s: '☮', d: 'Barış' }, { s: '☪', d: 'Ay Yıldız' }, { s: '✝', d: 'Latin Haç' },
    { s: '✡', d: 'Davut Yıldızı' }, { s: '☸', d: 'Dharma Çarkı' }, { s: '⚛', d: 'Atom' }, { s: '☥', d: 'Ankh' },
    
    // Tehlike ve uyarı
    { s: '☠', d: 'Kuru Kafa' }, { s: '⚠', d: 'Uyarı' }, { s: '⚡', d: 'Elektrik Tehlikesi' }, { s: '☢', d: 'Radyoaktif' },
    { s: '☣', d: 'Biyolojik Tehlike' }, { s: '⛔', d: 'Giriş Yok' }, { s: '🚫', d: 'Yasak' },
    
    // Diğer faydalı semboller
    { s: '∴', d: 'Öyleyse' }, { s: '∵', d: 'Çünkü' }, { s: '∶', d: 'Oran' }, { s: '∷', d: 'Orantı' },
    { s: '⌀', d: 'Çap' }, { s: '⏎', d: 'Return/Enter' }, { s: '⌫', d: 'Backspace' }, { s: '⌦', d: 'Delete Right' },
    { s: '⇥', d: 'Tab' }, { s: '⎋', d: 'Escape' }, { s: '⌘', d: 'Command (Mac)' }, { s: '⌥', d: 'Option (Mac)' },
    { s: '⇧', d: 'Shift' }, { s: '⌃', d: 'Control' }, { s: '␣', d: 'Boşluk' }, { s: '⏏', d: 'Çıkar' },
  ]
};
