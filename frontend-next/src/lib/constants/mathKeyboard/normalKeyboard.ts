import { MathKeyboardCategory } from './types';

// Normal Klavye Kategorileri - Kapsamlı özel karakter koleksiyonu

export const turkishSymbols: MathKeyboardCategory = {
  id: 'turkish',
  name: 'Türkçe',
  icon: 'Ş',
  symbols: [
    // Türkçe özel harfler
    { s: 'ş', d: 'Küçük Ş' }, { s: 'Ş', d: 'Büyük Ş' }, { s: 'ğ', d: 'Küçük Ğ' }, { s: 'Ğ', d: 'Büyük Ğ' },
    { s: 'ü', d: 'Küçük Ü' }, { s: 'Ü', d: 'Büyük Ü' }, { s: 'ö', d: 'Küçük Ö' }, { s: 'Ö', d: 'Büyük Ö' },
    { s: 'ç', d: 'Küçük Ç' }, { s: 'Ç', d: 'Büyük Ç' }, { s: 'ı', d: 'Noktasız ı' }, { s: 'İ', d: 'Noktalı İ' },
    
    // Azerice ek harfler
    { s: 'ə', d: 'Schwa (Azerice)' }, { s: 'Ə', d: 'Büyük Schwa' },
    
    // Türkçe noktalama
    { s: '«', d: 'Sol Tırnak (Türkçe)' }, { s: '»', d: 'Sağ Tırnak (Türkçe)' }, { s: '„', d: 'Alt Tırnak' }, { s: '\u201C', d: 'Sol Çift Tırnak' },
    { s: '\u201D', d: 'Sağ Çift Tırnak' }, { s: '\u2018', d: 'Sol Tek Tırnak' }, { s: '\u2019', d: 'Sağ Tek Tırnak' },
  ]
};

export const accentedSymbols: MathKeyboardCategory = {
  id: 'accented',
  name: 'Vurgulu',
  icon: 'ñ',
  symbols: [
    // A varyasyonları
    { s: 'á', d: 'a Akut' }, { s: 'à', d: 'a Grav' }, { s: 'â', d: 'a Şapka' }, { s: 'ä', d: 'a Umlaut' },
    { s: 'ã', d: 'a Tilde' }, { s: 'å', d: 'a Halka' }, { s: 'ā', d: 'a Makron' }, { s: 'ă', d: 'a Breve' },
    { s: 'ą', d: 'a Kuyruk (Ogonek)' }, { s: 'Á', d: 'A Akut' }, { s: 'À', d: 'A Grav' }, { s: 'Â', d: 'A Şapka' },
    { s: 'Ä', d: 'A Umlaut' }, { s: 'Ã', d: 'A Tilde' }, { s: 'Å', d: 'A Halka' }, { s: 'Ā', d: 'A Makron' },
    
    // E varyasyonları
    { s: 'é', d: 'e Akut' }, { s: 'è', d: 'e Grav' }, { s: 'ê', d: 'e Şapka' }, { s: 'ë', d: 'e Umlaut' },
    { s: 'ē', d: 'e Makron' }, { s: 'ě', d: 'e Caron' }, { s: 'ę', d: 'e Ogonek' }, { s: 'ė', d: 'e Noktalı' },
    { s: 'É', d: 'E Akut' }, { s: 'È', d: 'E Grav' }, { s: 'Ê', d: 'E Şapka' }, { s: 'Ë', d: 'E Umlaut' },
    
    // I varyasyonları
    { s: 'í', d: 'i Akut' }, { s: 'ì', d: 'i Grav' }, { s: 'î', d: 'i Şapka' }, { s: 'ï', d: 'i Umlaut' },
    { s: 'ī', d: 'i Makron' }, { s: 'ĭ', d: 'i Breve' }, { s: 'į', d: 'i Ogonek' }, { s: 'ı', d: 'Noktasız i' },
    { s: 'Í', d: 'I Akut' }, { s: 'Ì', d: 'I Grav' }, { s: 'Î', d: 'I Şapka' }, { s: 'Ï', d: 'I Umlaut' },
    
    // O varyasyonları
    { s: 'ó', d: 'o Akut' }, { s: 'ò', d: 'o Grav' }, { s: 'ô', d: 'o Şapka' }, { s: 'õ', d: 'o Tilde' },
    { s: 'ø', d: 'o Çizgili (İskandinav)' }, { s: 'œ', d: 'OE Bitişik' }, { s: 'ō', d: 'o Makron' }, { s: 'ő', d: 'o Çift Akut' },
    { s: 'Ó', d: 'O Akut' }, { s: 'Ò', d: 'O Grav' }, { s: 'Ô', d: 'O Şapka' }, { s: 'Õ', d: 'O Tilde' },
    { s: 'Ø', d: 'O Çizgili' }, { s: 'Œ', d: 'OE Bitişik (Büyük)' },
    
    // U varyasyonları
    { s: 'ú', d: 'u Akut' }, { s: 'ù', d: 'u Grav' }, { s: 'û', d: 'u Şapka' }, { s: 'ū', d: 'u Makron' },
    { s: 'ů', d: 'u Halka' }, { s: 'ű', d: 'u Çift Akut' }, { s: 'ų', d: 'u Ogonek' }, { s: 'ŭ', d: 'u Breve' },
    { s: 'Ú', d: 'U Akut' }, { s: 'Ù', d: 'U Grav' }, { s: 'Û', d: 'U Şapka' },
    
    // Diğer ünsüzler
    { s: 'ñ', d: 'n Tilde' }, { s: 'Ñ', d: 'N Tilde' }, { s: 'ß', d: 'Almanca Keskin S' }, { s: 'ẞ', d: 'Büyük Keskin S' },
    { s: 'ð', d: 'Eth (İzlanda)' }, { s: 'Ð', d: 'Büyük Eth' }, { s: 'þ', d: 'Thorn (İzlanda)' }, { s: 'Þ', d: 'Büyük Thorn' },
    { s: 'æ', d: 'AE Bitişik' }, { s: 'Æ', d: 'AE Bitişik (Büyük)' }, { s: 'ý', d: 'y Akut' }, { s: 'ÿ', d: 'y Umlaut' },
    
    // Slav dilleri
    { s: 'č', d: 'c Caron' }, { s: 'Č', d: 'C Caron' }, { s: 'ď', d: 'd Caron' }, { s: 'ě', d: 'e Caron' },
    { s: 'ň', d: 'n Caron' }, { s: 'ř', d: 'r Caron' }, { s: 'š', d: 's Caron' }, { s: 'Š', d: 'S Caron' },
    { s: 'ť', d: 't Caron' }, { s: 'ů', d: 'u Halka' }, { s: 'ž', d: 'z Caron' }, { s: 'Ž', d: 'Z Caron' },
    
    // Lehçe
    { s: 'ć', d: 'c Akut' }, { s: 'ł', d: 'l Çizgili' }, { s: 'Ł', d: 'L Çizgili' }, { s: 'ń', d: 'n Akut' },
    { s: 'ś', d: 's Akut' }, { s: 'ź', d: 'z Akut' }, { s: 'ż', d: 'z Noktalı' },
  ]
};

export const punctuationSymbols: MathKeyboardCategory = {
  id: 'punctuation',
  name: 'Noktalama',
  icon: '…',
  symbols: [
    // Temel noktalama
    { s: '.', d: 'Nokta' }, { s: ',', d: 'Virgül' }, { s: ';', d: 'Noktalı Virgül' }, { s: ':', d: 'İki Nokta' },
    { s: '!', d: 'Ünlem' }, { s: '?', d: 'Soru İşareti' }, { s: '¡', d: 'Ters Ünlem' }, { s: '¿', d: 'Ters Soru' },
    { s: '‽', d: 'Interrobang' }, { s: '⸘', d: 'Ters Interrobang' },
    
    // Tırnak işaretleri
    { s: '"', d: 'Düz Çift Tırnak' }, { s: "'", d: 'Düz Tek Tırnak' }, { s: '\u201C', d: 'Sol Çift Tırnak' }, { s: '\u201D', d: 'Sağ Çift Tırnak' },
    { s: '\u2018', d: 'Sol Tek Tırnak' }, { s: '\u2019', d: 'Sağ Tek Tırnak' }, { s: '„', d: 'Alt Çift Tırnak' }, { s: '‚', d: 'Alt Tek Tırnak' },
    { s: '«', d: 'Sol Guillemet' }, { s: '»', d: 'Sağ Guillemet' }, { s: '‹', d: 'Sol Tek Guillemet' }, { s: '›', d: 'Sağ Tek Guillemet' },
    { s: '「', d: 'Sol Köşe Tırnak (CJK)' }, { s: '」', d: 'Sağ Köşe Tırnak (CJK)' }, { s: '『', d: 'Sol Beyaz Köşe' }, { s: '』', d: 'Sağ Beyaz Köşe' },
    
    // Tireler
    { s: '-', d: 'Tire-Kısa Çizgi' }, { s: '–', d: 'En Tire' }, { s: '—', d: 'Em Tire' }, { s: '―', d: 'Yatay Çizgi' },
    { s: '‐', d: 'Tire (Unicode)' }, { s: '‑', d: 'Kırılmaz Tire' }, { s: '‒', d: 'Figure Tire' }, { s: '⁃', d: 'Hyphen Bullet' },
    { s: '−', d: 'Eksi İşareti' }, { s: '⁻', d: 'Üst İndis Eksi' }, { s: '₋', d: 'Alt İndis Eksi' },
    
    // Noktalar ve üç nokta
    { s: '…', d: 'Üç Nokta (Ellipsis)' }, { s: '‥', d: 'İki Nokta (Horizontal)' }, { s: '⋯', d: 'Orta Üç Nokta' }, { s: '⋮', d: 'Dikey Üç Nokta' },
    { s: '⋰', d: 'Yukarı Çapraz Üç Nokta' }, { s: '⋱', d: 'Aşağı Çapraz Üç Nokta' }, { s: '·', d: 'Orta Nokta' }, { s: '•', d: 'Bullet' },
    { s: '‧', d: 'Hyphenation Point' }, { s: '․', d: 'Tek Nokta Lider' }, { s: '‥', d: 'İki Nokta Lider' }, { s: '…', d: 'Üç Nokta Lider' },
    
    // Slash ve kesme
    { s: '/', d: 'Slash' }, { s: '\\', d: 'Backslash' }, { s: '|', d: 'Dikey Çizgi' }, { s: '¦', d: 'Kesik Dikey' },
    { s: '‖', d: 'Çift Dikey' }, { s: '⁄', d: 'Kesir Slash' }, { s: '∕', d: 'Bölme Slash' },
    
    // Özel noktalama
    { s: '§', d: 'Bölüm İşareti' }, { s: '¶', d: 'Paragraf İşareti' }, { s: '†', d: 'Hançer' }, { s: '‡', d: 'Çift Hançer' },
    { s: '※', d: 'Referans İşareti' }, { s: '⁂', d: 'Asterism' }, { s: '⁕', d: 'Çiçek Asterisk' }, { s: '⁎', d: 'Düşük Asterisk' },
    { s: '&', d: 'Ve İşareti (Ampersand)' }, { s: '@', d: 'At İşareti' }, { s: '#', d: 'Hash/Numara' }, { s: '№', d: 'Numero' },
  ]
};

export const emojiSymbols: MathKeyboardCategory = {
  id: 'emoji',
  name: 'Emoji',
  icon: '☺',
  symbols: [
    // Yüz ifadeleri
    { s: '☺', d: 'Gülümseyen Yüz' }, { s: '☻', d: 'Siyah Gülümseyen' }, { s: '☹', d: 'Üzgün Yüz' }, { s: '😀', d: 'Gülen Yüz' },
    { s: '😃', d: 'Gülen Gözler' }, { s: '😄', d: 'Gülen Yüz Kapalı Göz' }, { s: '😁', d: 'Sırıtan' }, { s: '😆', d: 'Kahkaha' },
    { s: '😅', d: 'Terli Gülen' }, { s: '🤣', d: 'Yerde Yuvarlanan' }, { s: '😂', d: 'Sevinç Gözyaşı' }, { s: '🙂', d: 'Hafif Gülümseyen' },
    { s: '😊', d: 'Kızaran Gülümseyen' }, { s: '😇', d: 'Hale' }, { s: '🥰', d: 'Kalplerle Gülümseyen' }, { s: '😍', d: 'Kalp Gözler' },
    { s: '😘', d: 'Öpücük Atan' }, { s: '😗', d: 'Öpen Yüz' }, { s: '😜', d: 'Dil Çıkaran Göz Kırpan' }, { s: '😝', d: 'Dil Çıkaran Kapalı Göz' },
    { s: '😎', d: 'Güneş Gözlüğü' }, { s: '🤓', d: 'İnek' }, { s: '🧐', d: 'Monoküllü' }, { s: '😏', d: 'Sırıtan' },
    { s: '😒', d: 'Memnuniyetsiz' }, { s: '😔', d: 'Düşünceli' }, { s: '😢', d: 'Ağlayan' }, { s: '😭', d: 'Hüngür Ağlayan' },
    { s: '😱', d: 'Korku' }, { s: '😡', d: 'Öfkeli' }, { s: '🤔', d: 'Düşünen' }, { s: '🤗', d: 'Kucaklayan' },
    
    // El işaretleri
    { s: '👍', d: 'Beğeni' }, { s: '👎', d: 'Beğenmeme' }, { s: '👏', d: 'Alkış' }, { s: '🙌', d: 'Eller Havada' },
    { s: '👋', d: 'El Sallama' }, { s: '✋', d: 'Açık El' }, { s: '🤚', d: 'El Arkası' }, { s: '🖐', d: 'Açık Parmaklar' },
    { s: '✌', d: 'Zafer/Barış' }, { s: '🤞', d: 'Şans' }, { s: '🤟', d: 'Seni Seviyorum' }, { s: '🤘', d: 'Rock' },
    { s: '👆', d: 'Yukarı İşaret' }, { s: '👇', d: 'Aşağı İşaret' }, { s: '👈', d: 'Sol İşaret' }, { s: '👉', d: 'Sağ İşaret' },
    { s: '👌', d: 'OK İşareti' }, { s: '🤏', d: 'Çimdik' }, { s: '✊', d: 'Yumruk' }, { s: '👊', d: 'Yumruk (Önden)' },
    { s: '💪', d: 'Pazı' }, { s: '🙏', d: 'Dua/Teşekkür' }, { s: '🤝', d: 'Tokalaşma' }, { s: '✍', d: 'Yazma' },
    
    // Kalp ve duygular
    { s: '❤', d: 'Kırmızı Kalp' }, { s: '🧡', d: 'Turuncu Kalp' }, { s: '💛', d: 'Sarı Kalp' }, { s: '💚', d: 'Yeşil Kalp' },
    { s: '💙', d: 'Mavi Kalp' }, { s: '💜', d: 'Mor Kalp' }, { s: '🖤', d: 'Siyah Kalp' }, { s: '🤍', d: 'Beyaz Kalp' },
    { s: '💔', d: 'Kırık Kalp' }, { s: '💕', d: 'İki Kalp' }, { s: '💖', d: 'Parıldayan Kalp' }, { s: '💗', d: 'Büyüyen Kalp' },
    { s: '💘', d: 'Ok Saplamış Kalp' }, { s: '💝', d: 'Kurdeleli Kalp' }, { s: '💞', d: 'Dönen Kalpler' }, { s: '💟', d: 'Kalp Süslemesi' },
    
    // Doğa ve hava
    { s: '🌸', d: 'Kiraz Çiçeği' }, { s: '🌹', d: 'Gül' }, { s: '🌺', d: 'Hibiskus' }, { s: '🌻', d: 'Ayçiçeği' },
    { s: '🌼', d: 'Papatya' }, { s: '🌷', d: 'Lale' }, { s: '🌱', d: 'Fide' }, { s: '🌲', d: 'Yaprak Döken Ağaç' },
    { s: '🌳', d: 'Yapraklı Ağaç' }, { s: '🌴', d: 'Palmiye' }, { s: '🌵', d: 'Kaktüs' }, { s: '🌾', d: 'Başak' },
    { s: '☀', d: 'Güneş' }, { s: '🌙', d: 'Hilal' }, { s: '⭐', d: 'Yıldız' }, { s: '🌟', d: 'Parlayan Yıldız' },
    { s: '✨', d: 'Parıltılar' }, { s: '⚡', d: 'Yıldırım' }, { s: '🔥', d: 'Ateş' }, { s: '💧', d: 'Damla' },
    { s: '🌈', d: 'Gökkuşağı' }, { s: '☁', d: 'Bulut' }, { s: '❄', d: 'Kar Tanesi' }, { s: '🌊', d: 'Dalga' },
  ]
};

export const mathOperatorsSymbols: MathKeyboardCategory = {
  id: 'mathops',
  name: 'Operatörler',
  icon: '⊕',
  symbols: [
    // Toplama çeşitleri
    { s: '+', d: 'Artı' }, { s: '±', d: 'Artı Eksi' }, { s: '∓', d: 'Eksi Artı' }, { s: '⊕', d: 'Daire Artı (XOR)' },
    { s: '⊞', d: 'Kare Artı' }, { s: '⨁', d: 'N-ary Daire Artı' }, { s: '∔', d: 'Nokta Artı' }, { s: '⧺', d: 'Çift Artı' },
    { s: '⧻', d: 'Üçlü Artı' },
    
    // Çıkarma/eksi çeşitleri
    { s: '-', d: 'Tire-Eksi' }, { s: '−', d: 'Eksi İşareti' }, { s: '⊖', d: 'Daire Eksi' }, { s: '⊟', d: 'Kare Eksi' },
    { s: '∸', d: 'Nokta Eksi' }, { s: '⨪', d: 'Eksi İşaret (Alt)' },
    
    // Çarpma çeşitleri
    { s: '×', d: 'Çarpı' }, { s: '·', d: 'Orta Nokta' }, { s: '∙', d: 'Bullet Operatör' }, { s: '⋅', d: 'Nokta Operatör' },
    { s: '⊗', d: 'Daire Çarpı (Tensör)' }, { s: '⊠', d: 'Kare Çarpı' }, { s: '⨂', d: 'N-ary Daire Çarpı' }, { s: '∗', d: 'Asterisk Operatör' },
    { s: '⋆', d: 'Yıldız Operatör' }, { s: '★', d: 'Siyah Yıldız' }, { s: '⊛', d: 'Daire Asterisk' },
    
    // Bölme çeşitleri
    { s: '÷', d: 'Bölme' }, { s: '/', d: 'Slash' }, { s: '⁄', d: 'Kesir Slash' }, { s: '∕', d: 'Bölme Slash' },
    { s: '⊘', d: 'Daire Bölme' }, { s: '⌿', d: 'Slash Kesme' }, { s: '⧵', d: 'Ters Bölme (Set)' },
    
    // Daire operatörleri
    { s: '⊙', d: 'Noktalı Daire' }, { s: '⊚', d: 'Halkalı Daire' }, { s: '⊜', d: 'Eşitlikli Daire' }, { s: '⊝', d: 'Çizgili Daire' },
    { s: '⦶', d: 'Daire Dikey Çizgi' }, { s: '⦷', d: 'Daire Paralel' }, { s: '⦸', d: 'Daire Dik' }, { s: '⦹', d: 'Daire Ters Bölme' },
    
    // Kare operatörleri
    { s: '⊡', d: 'Noktalı Kare' }, { s: '⊓', d: 'Kare Cap' }, { s: '⊔', d: 'Kare Cup' }, { s: '⧆', d: 'İki Birleşik Kare' },
    
    // Birleşim/Kesişim
    { s: '∪', d: 'Birleşim (Cup)' }, { s: '∩', d: 'Kesişim (Cap)' }, { s: '⊎', d: 'Artılı Birleşim' }, { s: '⊌', d: 'Birleşim (Alt)' },
    { s: '⋃', d: 'Büyük Birleşim' }, { s: '⋂', d: 'Büyük Kesişim' },
    
    // Çeşitli operatörler
    { s: '∘', d: 'Kompozisyon' }, { s: '∝', d: 'Orantılı' }, { s: '√', d: 'Karekök' }, { s: '∛', d: 'Küpkök' },
    { s: '∜', d: 'Dördüncü Kök' }, { s: '∟', d: 'Dik Açı' }, { s: '∠', d: 'Açı' }, { s: '⊾', d: 'Dik Açı (Yay)' },
    { s: '⊿', d: 'Dik Üçgen' }, { s: '∡', d: 'Ölçülen Açı' }, { s: '∢', d: 'Küresel Açı' },
  ]
};

// Normal klavye için tüm kategorileri birleştir
export const NORMAL_KEYBOARD_CATEGORIES: MathKeyboardCategory[] = [
  turkishSymbols,
  accentedSymbols,
  punctuationSymbols,
  emojiSymbols,
  mathOperatorsSymbols,
];
