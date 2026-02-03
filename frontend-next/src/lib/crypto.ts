/**
 * Client-Side Encryption Utilities
 * ================================
 * 
 * Bu modül not ve klasör içeriklerini şifrelemek için kullanılır.
 * AES-GCM algoritması ile şifreleme yapılır.
 * 
 * ÖNEMLİ: Şifreleme tamamen client-side yapılır, backend ve AI bu verileri okuyamaz.
 * Şifre kaybedilirse veri kurtarılamaz!
 */

// AES-GCM ile şifreleme parametreleri
const ALGORITHM = 'AES-GCM';
const KEY_LENGTH = 256;
const SALT_LENGTH = 16;
const IV_LENGTH = 12;
const ITERATIONS = 100000;

/**
 * Şifreden AES anahtarı türetir (PBKDF2)
 */
async function deriveKey(password: string, salt: Uint8Array): Promise<CryptoKey> {
  const encoder = new TextEncoder();
  const passwordKey = await crypto.subtle.importKey(
    'raw',
    encoder.encode(password),
    'PBKDF2',
    false,
    ['deriveKey']
  );

  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: salt.buffer as ArrayBuffer,
      iterations: ITERATIONS,
      hash: 'SHA-256',
    },
    passwordKey,
    { name: ALGORITHM, length: KEY_LENGTH },
    false,
    ['encrypt', 'decrypt']
  );
}

/**
 * Metni şifreler
 * @param plaintext Şifrelenecek metin
 * @param password Kullanıcının şifresi
 * @returns Base64 encoded şifreli veri (salt + iv + ciphertext)
 */
export async function encryptText(plaintext: string, password: string): Promise<string> {
  const encoder = new TextEncoder();
  
  // Rastgele salt ve IV oluştur
  const salt = crypto.getRandomValues(new Uint8Array(SALT_LENGTH));
  const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH));
  
  // Şifreden anahtar türet
  const key = await deriveKey(password, salt);
  
  // Şifrele
  const ciphertext = await crypto.subtle.encrypt(
    { name: ALGORITHM, iv },
    key,
    encoder.encode(plaintext)
  );
  
  // Salt + IV + Ciphertext birleştir
  const combined = new Uint8Array(salt.length + iv.length + ciphertext.byteLength);
  combined.set(salt, 0);
  combined.set(iv, salt.length);
  combined.set(new Uint8Array(ciphertext), salt.length + iv.length);
  
  // Base64 encode
  return btoa(String.fromCharCode.apply(null, Array.from(combined)));
}

/**
 * Şifreli metni çözer
 * @param encryptedData Base64 encoded şifreli veri
 * @param password Kullanıcının şifresi
 * @returns Çözülmüş metin veya null (yanlış şifre)
 */
export async function decryptText(encryptedData: string, password: string): Promise<string | null> {
  try {
    // Base64 decode
    const combined = new Uint8Array(
      atob(encryptedData).split('').map(c => c.charCodeAt(0))
    );
    
    // Salt, IV ve ciphertext ayır
    const salt = combined.slice(0, SALT_LENGTH);
    const iv = combined.slice(SALT_LENGTH, SALT_LENGTH + IV_LENGTH);
    const ciphertext = combined.slice(SALT_LENGTH + IV_LENGTH);
    
    // Şifreden anahtar türet
    const key = await deriveKey(password, salt);
    
    // Şifre çöz
    const decrypted = await crypto.subtle.decrypt(
      { name: ALGORITHM, iv },
      key,
      ciphertext
    );
    
    const decoder = new TextDecoder();
    return decoder.decode(decrypted);
  } catch (error) {
    // Yanlış şifre veya bozuk veri
    console.error('Decryption failed:', error);
    return null;
  }
}

/**
 * Verinin şifreli olup olmadığını kontrol eder
 * Şifreli veriler "ENC:" prefixi ile başlar
 */
export function isEncryptedContent(content: string): boolean {
  return content.startsWith('ENC:');
}

/**
 * Şifreli içeriği işaretler
 */
export function markAsEncrypted(encryptedContent: string): string {
  return `ENC:${encryptedContent}`;
}

/**
 * Şifreli içerik işaretini kaldırır
 */
export function removeEncryptionMark(content: string): string {
  if (content.startsWith('ENC:')) {
    return content.slice(4);
  }
  return content;
}

/**
 * İçeriği şifreler ve işaretler
 */
export async function encryptContent(content: string, password: string): Promise<string> {
  const encrypted = await encryptText(content, password);
  return markAsEncrypted(encrypted);
}

/**
 * Şifreli içeriği çözer
 */
export async function decryptContent(content: string, password: string): Promise<string | null> {
  if (!isEncryptedContent(content)) {
    return content;
  }
  const encryptedData = removeEncryptionMark(content);
  return decryptText(encryptedData, password);
}

/**
 * Basit şifre doğrulama (minimum gereksinimler)
 */
export function validatePassword(password: string): { valid: boolean; message?: string } {
  if (password.length < 4) {
    return { valid: false, message: 'Şifre en az 4 karakter olmalı' };
  }
  return { valid: true };
}
