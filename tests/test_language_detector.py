"""
Language Detector Unit Tests
Dil Algılama Modülü Birim Testleri
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.language_detector import (
    detect_language,
    detect_language_detailed,
    Language,
    is_turkish,
    is_english,
    get_system_prompt_for_language
)


class TestLanguageDetection:
    """Dil algılama testleri."""
    
    # === Türkçe Testleri ===
    
    def test_turkish_with_special_chars(self):
        """Türkçe özel karakterli metin."""
        assert detect_language("Merhaba, nasılsın?") == Language.TURKISH
        assert detect_language("Bana ilginç filmler önerir misin?") == Language.TURKISH
        assert detect_language("Şu dosyayı çevir") == Language.TURKISH
        assert detect_language("Türkçe öğreniyorum") == Language.TURKISH
    
    def test_turkish_without_special_chars(self):
        """Özel karakter olmadan Türkçe."""
        assert detect_language("Ben bir ogrenci") == Language.TURKISH  # No special chars but Turkish keywords
        assert detect_language("Bu nedir") == Language.TURKISH
        assert detect_language("Bana yardim et") == Language.TURKISH
    
    def test_turkish_questions(self):
        """Türkçe soru cümleleri."""
        assert detect_language("Ne zaman başlıyor?") == Language.TURKISH
        assert detect_language("Nasıl yapılır?") == Language.TURKISH
        assert detect_language("Neden böyle oldu?") == Language.TURKISH
        assert detect_language("Kim geldi?") == Language.TURKISH
    
    def test_turkish_with_keywords(self):
        """Türkçe anahtar kelimelerle tespit."""
        assert detect_language("bir iki ve üç") == Language.TURKISH
        assert detect_language("lütfen yardım et") == Language.TURKISH
        assert detect_language("evet yapabilirim") == Language.TURKISH
    
    # === İngilizce Testleri ===
    
    def test_english_basic(self):
        """Temel İngilizce metinler."""
        assert detect_language("Hello, how are you?") == Language.ENGLISH
        assert detect_language("What is the weather today?") == Language.ENGLISH
        assert detect_language("Can you help me with this?") == Language.ENGLISH
    
    def test_english_questions(self):
        """İngilizce soru cümleleri."""
        assert detect_language("What time is it?") == Language.ENGLISH
        assert detect_language("How does this work?") == Language.ENGLISH
        assert detect_language("Why did you do that?") == Language.ENGLISH
        assert detect_language("Where can I find it?") == Language.ENGLISH
    
    def test_english_technical(self):
        """Teknik İngilizce metinler."""
        assert detect_language("Please translate this document") == Language.ENGLISH
        assert detect_language("Show me the code") == Language.ENGLISH
        assert detect_language("Explain how the algorithm works") == Language.ENGLISH
    
    # === Edge Cases ===
    
    def test_empty_text(self):
        """Boş metin."""
        assert detect_language("") == Language.UNKNOWN
        assert detect_language("   ") == Language.UNKNOWN
    
    def test_single_word_turkish(self):
        """Tek kelime Türkçe."""
        assert detect_language("Merhaba") == Language.TURKISH
        assert detect_language("Teşekkürler") == Language.TURKISH
    
    def test_single_word_english(self):
        """Tek kelime İngilizce."""
        assert detect_language("Hello") == Language.ENGLISH
        assert detect_language("Thanks") == Language.ENGLISH
    
    def test_mixed_language(self):
        """Karışık dil metinler - Türkçe karakterler baskın olmalı."""
        # Turkish chars present = Turkish
        assert detect_language("Hello dünya") == Language.TURKISH
        assert detect_language("Meeting için hazırlan") == Language.TURKISH
    
    # === Detailed Detection Tests ===
    
    def test_confidence_with_turkish_chars(self):
        """Türkçe karakterlerle yüksek güven."""
        result = detect_language_detailed("Merhaba, nasılsın?")
        assert result.language == Language.TURKISH
        assert result.confidence >= 0.7
    
    def test_confidence_with_keywords(self):
        """Keyword eşleşmesiyle güven."""
        result = detect_language_detailed("What is this about?")
        assert result.language == Language.ENGLISH
        assert result.confidence >= 0.5
    
    # === Helper Function Tests ===
    
    def test_is_turkish(self):
        """is_turkish helper fonksiyonu."""
        assert is_turkish("Merhaba") == True
        assert is_turkish("Hello") == False
    
    def test_is_english(self):
        """is_english helper fonksiyonu."""
        assert is_english("Hello") == True
        assert is_english("Merhaba") == False
    
    # === System Prompt Tests ===
    
    def test_system_prompt_turkish(self):
        """Türkçe system prompt."""
        prompt = get_system_prompt_for_language(Language.TURKISH)
        assert "TÜRKÇE" in prompt
        assert "ZORUNLU KURALLAR" in prompt
        assert "ÇOKLU GÖREV" in prompt
    
    def test_system_prompt_english(self):
        """İngilizce system prompt."""
        prompt = get_system_prompt_for_language(Language.ENGLISH)
        assert "English" in prompt
        assert "MANDATORY RULES" in prompt
        assert "MULTI-TASK" in prompt


class TestRealWorldScenarios:
    """Gerçek dünya senaryoları."""
    
    def test_film_recommendation_turkish(self):
        """Film önerisi isteği - Türkçe."""
        query = "Bana ilginç filmler önerir misin, bunun için interneti tara"
        assert detect_language(query) == Language.TURKISH
    
    def test_translation_request_turkish(self):
        """Çeviri isteği - Türkçe."""
        query = "İkisini de Türkçeye çevir"
        assert detect_language(query) == Language.TURKISH
    
    def test_code_help_english(self):
        """Kod yardımı - İngilizce."""
        query = "How do I fix this Python error?"
        assert detect_language(query) == Language.ENGLISH
    
    def test_document_analysis_turkish(self):
        """Doküman analizi - Türkçe."""
        query = "Bu dosyayı analiz et ve bana özet çıkar"
        assert detect_language(query) == Language.TURKISH


class TestLanguageOverride:
    """Dil override testleri - kullanıcı açıkça farklı dil istediğinde."""
    
    from core.language_detector import detect_requested_language
    
    def test_turkish_query_english_response_request(self):
        """Türkçe soru, İngilizce yanıt isteği."""
        from core.language_detector import detect_requested_language
        
        # Türkçe ifadeler
        assert detect_requested_language("Film öner ama ingilizce yanıt ver") == Language.ENGLISH
        assert detect_requested_language("Bunu açıkla, ingilizce cevap istiyorum") == Language.ENGLISH
        assert detect_requested_language("Analiz et ve yanıtı ingilizce yaz") == Language.ENGLISH
    
    def test_english_query_turkish_response_request(self):
        """İngilizce soru, Türkçe yanıt isteği."""
        from core.language_detector import detect_requested_language
        
        # English expressions for Turkish response
        assert detect_requested_language("Explain this but respond in turkish") == Language.TURKISH
        assert detect_requested_language("What is this? Answer in Turkish please") == Language.TURKISH
    
    def test_no_override_request(self):
        """Override talebi olmayan sorgular."""
        from core.language_detector import detect_requested_language
        
        assert detect_requested_language("Merhaba, nasılsın?") is None
        assert detect_requested_language("Hello, how are you?") is None
        assert detect_requested_language("Film önerir misin?") is None
    
    def test_english_request_patterns(self):
        """İngilizce yanıt kalıpları."""
        from core.language_detector import detect_requested_language
        
        assert detect_requested_language("respond in english please") == Language.ENGLISH
        assert detect_requested_language("give me an english response") == Language.ENGLISH
        assert detect_requested_language("cevabı ingilizce ver") == Language.ENGLISH
    
    def test_turkish_request_patterns(self):
        """Türkçe yanıt kalıpları."""
        from core.language_detector import detect_requested_language
        
        assert detect_requested_language("answer in turkish") == Language.TURKISH
        assert detect_requested_language("turkish response please") == Language.TURKISH


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
